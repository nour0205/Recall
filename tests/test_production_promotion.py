"""Production contracts with stubbed infrastructure; no API tokens or indexes."""
import ast
import importlib.util
import json
import os
from pathlib import Path
import sys
from types import ModuleType
import unittest
from unittest.mock import Mock, patch

# app.config requires a key at import; nothing here calls OpenAI.
os.environ.setdefault("OPENAI_API_KEY", "test-placeholder")

from app.orchestration import prompts
from app.rag import hybrid_retriever as hybrid
from app.schemas.api import QuestionRequest
from app.schemas.retrieval import RetrievedChunk


def load_api():
    llm = ModuleType('app.llm.client')
    llm.chat = Mock()
    chroma = ModuleType('app.vectordb.chroma_store')
    chroma.ChromaStore = Mock()
    embedder = ModuleType('app.embeddings.embedder')
    embedder.embed_texts = Mock()
    with patch.dict(sys.modules, {'app.llm.client': llm, 'app.vectordb.chroma_store': chroma,
                                  'app.embeddings.embedder': embedder}):
        spec = importlib.util.spec_from_file_location('production_api_under_test', 'app/api/main.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module


def chunks():
    return [RetrievedChunk(id=str(i), chunk_id=str(i), document_id='notes', chunk_index=i,
                           text=f'Supplied factual point {i}', retrieval_type='hybrid', hybrid_score=0.03)
            for i in range(5)]


class ProductionPromotionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.api = load_api()

    def setUp(self):
        self.rows = chunks()
        self.retrieve = patch.object(self.api, 'hybrid_retrieve', return_value=self.rows).start()
        self.chat = patch.object(self.api, 'chat', return_value='Supplied point 0 [S1] and point 1 [S2].').start()
        self.fallback = patch.object(self.api, 'rag_answer_with_sources', side_effect=AssertionError('Unexpected fallback')).start()
        self.addCleanup(patch.stopall)

    def test_default_ask_uses_hybrid_top5_and_preserves_all_chunks_labels_and_schema(self):
        from fastapi.testclient import TestClient
        with TestClient(self.api.app) as client:
            response = client.post('/ask', json={'question':'Explain both supplied points'})
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(set(result), {'answer','sources','route','study_hint'})
        self.assertEqual(len(result['sources']), 5)  # Same document is not deduplicated.
        self.assertEqual([s['text'] for s in result['sources']], [r.text for r in self.rows])
        self.assertEqual(set(result['sources'][0]), {'document_id','chunk_index','text','retrieval_type','hybrid_score','rerank_score'})
        self.retrieve.assert_called_once_with(store=self.api.store, question='Explain both supplied points', k=5, where=None, candidate_k=10)
        message = self.chat.call_args.args[0][1]['content']
        for i, row in enumerate(self.rows, 1):
            self.assertIn(f'[S{i}] DOCUMENT: {row.document_id}\nCONTENT:\n{row.text}', message)

    def test_ask_makes_a_single_model_call_and_has_no_planner(self):
        result = self.api.ask(QuestionRequest(question='Explain both supplied points'))
        self.chat.assert_called_once()
        self.assertIsNone(result.route)
        self.assertFalse(hasattr(self.api, 'plan_question'))
        self.assertFalse(Path('app/orchestration/planner.py').exists())

    def test_owner_scope_combines_with_document_scope(self):
        self.api.ask(QuestionRequest(question='Where?',document_ids=['a','b'],owner='student'))
        self.assertEqual(self.retrieve.call_args.kwargs['where'], {'$and':[
            {'document_id':{'$in':['a','b']}}, {'owner':'student'}]})

    def test_explicit_document_scope_wins_and_multiple_ids_work(self):
        self.api.ask(QuestionRequest(question='Review',document_id='chosen',document_ids=['other']))
        self.assertEqual(self.retrieve.call_args.kwargs['where'], {'document_id':'chosen'})
        self.api.ask(QuestionRequest(question='Review',document_ids=['a','b','a']))
        self.assertEqual(self.retrieve.call_args.kwargs['where'], {'document_id':{'$in':['a','b']}})

    def test_refusal_is_exact_stops_trailing_content_and_never_falls_back(self):
        self.chat.return_value = "  I don't know.\nSupporting Points: unsupported details"
        result = self.api.ask(QuestionRequest(question='Unsupported request'))
        self.assertEqual(result.answer, "I don't know.")
        self.assertEqual(result.sources, [])
        self.assertIsNone(result.study_hint)
        self.chat.assert_called_once()
        self.fallback.assert_not_called()

    def test_absent_or_blank_context_refuses_without_generator_or_fallback(self):
        for rows in ([], [RetrievedChunk(id='empty',document_id='notes',text='  ')]):
            self.retrieve.return_value = rows
            result = self.api.ask(QuestionRequest(question='Unsupported'))
            self.assertEqual(result.answer,"I don't know.")
        self.chat.assert_not_called()
        self.fallback.assert_not_called()

    def test_supported_multi_part_response_is_preserved(self):
        result = self.api.ask(QuestionRequest(question='Identify the problem and its mechanism'))
        self.assertEqual(result.answer,self.chat.return_value)
        self.assertIsNotNone(result.study_hint)
        messages = self.chat.call_args.args[0]
        self.assertIn('answer each requested part',messages[0]['content'])
        self.assertIn('identification and a supported explanation/mechanism',messages[0]['content'])
        self.assertIn('Do not refuse when',messages[0]['content'])

    def test_generation_exception_uses_same_scoped_nonreranked_fallback(self):
        from app.schemas.api import RagAnswerResult
        self.chat.side_effect = RuntimeError('fixture outage')
        self.fallback.side_effect = None
        self.fallback.return_value = RagAnswerResult(answer="I don't know.",sources=[])
        result = self.api.ask(QuestionRequest(question='Q',document_id='notes'))
        self.assertEqual(result.answer,"I don't know.")
        self.fallback.assert_called_once_with(question='Q',store=self.api.store,k=5,where={'document_id':'notes'})

    def test_critical_prompt_rules_no_benchmark_metadata_and_no_forced_expansion(self):
        messages = prompts.build_answer_prompt('A user question',self.rows,'exam_preparation')
        system = messages[0]['content']
        for rule in ('Use ONLY facts explicitly supported','Do not add explanations, mechanisms, examples, formulas',
                     'Every substantive factual claim','Preserve qualifiers','may, can, often, or usually',
                     "I don't know.\nStop immediately after this sentence.",'Do not infer facts',
                     'Prefer a short, direct answer','dependency/problem itself','not explicitly requested'):
            self.assertIn(rule,system)
        serialized = json.dumps(messages)
        for forbidden in ('retrieval_001','reference_answer','required_points','evidence_group_ids','completeness_score',
                          '## Supporting Points','## Review Tip','## Common Exam Traps'):
            self.assertNotIn(forbidden,serialized)
        tree = ast.parse(Path(prompts.__file__).read_text(encoding='utf-8'))
        self.assertFalse(any(isinstance(n,ast.ImportFrom) and (n.module or '').startswith('evaluation') for n in ast.walk(tree)))

    def test_real_dense_bm25_rrf_path_keeps_fused_order_without_rerankers(self):
        store = Mock()
        vector = [{'id':'shared','rank':1,'document':'vector text','metadata':{'document_id':'notes'}},
                  {'id':'vector','rank':2,'document':'V','metadata':{'document_id':'notes'}}]
        sparse = [{'id':'shared','rank':1,'text':'sparse text','metadata':{'document_id':'notes'}},
                  {'id':'sparse','rank':2,'text':'B','metadata':{'document_id':'notes'}}]
        store.query_with_scores.return_value = vector
        with patch.object(hybrid,'embed_texts',return_value=[[0.1]]), patch.object(hybrid,'search_whoosh',return_value=sparse) as bm25:
            rows = hybrid.hybrid_retrieve(store,'Q',k=5,candidate_k=10)
        self.assertEqual([r.id for r in rows],['shared','vector','sparse'])
        self.assertAlmostEqual(rows[0].hybrid_score,2/61)
        self.assertEqual(store.query_with_scores.call_args.kwargs['k'],10)
        bm25.assert_called_once_with('Q',limit=10)
        for path in ('app/api/main.py','app/rag/pipeline.py','app/rag/hybrid_retriever.py'):
            tree = ast.parse(Path(path).read_text(encoding='utf-8'))
            for node in ast.walk(tree):
                if isinstance(node,ast.ImportFrom):
                    self.assertNotIn('reranker',node.module or '')
                    self.assertNotIn('semantic',node.module or '')

    def test_sparse_scope_matches_chroma_and_including_owner(self):
        where = {'$and':[{'document_id':{'$in':['a','b']}},{'owner':'student'}]}
        candidates = [{'id':str(i),'text':'T','metadata':m} for i,m in enumerate([
            {'document_id':'a','owner':'student'},{'document_id':'b','owner':'other'},
            {'document_id':'c','owner':'student'}])]
        with patch.object(hybrid,'search_whoosh',return_value=candidates):
            result = hybrid.retrieve_bm25_candidates('Q',k=10,where=where)
        self.assertEqual([r['id'] for r in result],['0'])

    def test_fallback_uses_plain_hybrid_and_same_prompt(self):
        from app.rag import pipeline
        with patch.object(pipeline,'hybrid_retrieve',return_value=self.rows) as retrieve, patch.object(pipeline,'chat',return_value='Point [S1].') as chat:
            result = pipeline.rag_answer_with_sources('Q',Mock(),k=5)
            self.assertEqual(len(result.sources),5)
            self.assertEqual(retrieve.call_args.kwargs['candidate_k'],10)
            self.assertEqual(retrieve.call_args.kwargs['k'],5)
            self.assertIn('[S5]',chat.call_args.args[0][1]['content'])
            self.assertIn(prompts.SYSTEM_PROMPT,chat.call_args.args[0][0]['content'])
            chat.return_value="I don't know. More text"
            refusal = pipeline.rag_answer_with_sources('Q',Mock(),k=5)
            self.assertEqual((refusal.answer, refusal.sources), ("I don't know.", []))

    def test_ingest_and_delete_endpoints_use_the_library(self):
        # Index behaviour itself is tested on real indexes in tests/test_library.py.
        from fastapi.testclient import TestClient
        from app.library import IngestionError
        with TestClient(self.api.app) as client:
            with patch.object(self.api, 'add_document', return_value={'status':'ingested','chunks_added':2}) as add:
                self.assertEqual(client.post('/ingest', json={'document_id':'n','text':'Notes.'}).json()['status'], 'ingested')
                self.assertIs(add.call_args.kwargs['embed'], self.api.embed_texts)
            with patch.object(self.api, 'add_document', side_effect=IngestionError('rolled back')):
                failed = client.post('/ingest', json={'document_id':'n','text':'Notes.'})
                self.assertEqual((failed.status_code, failed.json()['detail']), (500, 'rolled back'))
            with patch.object(self.api, 'remove_document', return_value={'vector_chunks_deleted':0,'bm25_chunks_deleted':0}):
                self.assertEqual(client.delete('/documents/missing').status_code, 404)
            with patch.object(self.api, 'remove_document', return_value={'vector_chunks_deleted':2,'bm25_chunks_deleted':2}):
                deleted = client.delete('/documents/n').json()
                self.assertEqual((deleted['status'], deleted['bm25_chunks_deleted']), ('deleted', 2))

    def test_fallback_empty_context_refuses_without_model(self):
        from app.rag import pipeline
        with patch.object(pipeline,'hybrid_retrieve',return_value=[]), patch.object(pipeline,'chat') as chat:
            result = pipeline.rag_answer_with_sources('Q',Mock(),k=5)
        self.assertEqual(result.answer,"I don't know.")
        self.assertEqual(result.sources,[])
        chat.assert_not_called()
