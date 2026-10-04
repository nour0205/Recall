# Retrieval failure analysis: nine differentiating queries

Source: evaluation\results\retrieval_v1_20261003T204707249551Z.json

Fresh diagnostic reconstruction using existing implementations, same candidate_k=10/k=5. Original run did not save scores. Vector distances are diagnostic, not historical measurements. Rank agreement is checked for each saved mode.

Vector distance: Chroma L2 distance (lower is closer). BM25: Whoosh BM25F score. RRF: sum of 1/(60+backend rank). Rerank: exact keyword count + phrase bonus + max(0,1-0.05*(fused rank-1)).

Score columns provide cross-backend diagnostic context. A dash means absent from that backend top-10 candidate pool; it does not mean the chunk has no embedding. Rerank scores appear only for reranked output. The shared normalized vector score is null because the adapter keeps distance under a different raw key.

## retrieval_002

When can accuracy be a misleading evaluation metric?

### Canonical evidence

**ml_model_evaluation / chunk 0 / `6d045457-927e-4d91-a801-80fb6b49a451`**

Model evaluation measures how well a machine learning model performs on unseen data. A model should not only fit the training data but also generalize to new examples. A confusion matrix summarizes classification results using true positives, true negatives, false positives, and false negatives. Accuracy measures the proportion of correct predictions. Accuracy can be misleading on imbalanced datasets. Precision measures how many predicted positive instances are actually positive.


### Alternatives from annotation notes

Canonical evidence defines accuracy and states that it can be misleading on imbalanced datasets. Full equivalent evidence: bd664c0a-5bcb-457d-b326-bddcb215638f (ml_model_evaluation, chunk 1) repeats both statements and is excluded from automatic scoring.

**ml_model_evaluation / chunk 1 / `bd664c0a-5bcb-457d-b326-bddcb215638f`**

Model evaluation measures how well a machine learning model performs on unseen data. A model should not only fit the training data but also generalize to new examples. A confusion matrix summarizes classification results using true positives, true negatives, false positives, and false negatives. Accuracy measures the proportion of correct predictions. Accuracy can be misleading on imbalanced datasets. Precision measures how many predicted positive instances are actually positive. Recall measures how many actual positive instances are correctly identified. The F1 score combines precision and recall into a single metric and is useful when both are important. Cross-validation is often used to obtain a more reliable estimate of model performance.


### Ranking and score tables

Rank agreement with saved results: {'vector': True, 'bm25': True, 'hybrid': True, 'hybrid_reranked': True}

Reranker non-stopword question tokens: when, can, accuracy, misleading, evaluation, metric

#### vector

| Rank | Document | Chunk UUID | Vector rank / distance | BM25 rank / score | RRF rank / score | Rerank score |
|---:|---|---|---|---|---|---:|
| 1 | ml_model_evaluation | `6d045457-927e-4d91-a801-80fb6b49a451` | 1 / 0.933049560 | 2 / 11.123085062 | 1 / 0.032522475 | - |
| 2 | ml_model_evaluation | `bd664c0a-5bcb-457d-b326-bddcb215638f` | 2 / 0.941775918 | 1 / 12.740429520 | 2 / 0.032522475 | - |
| 3 | ml_bias_variance_generalization | `7e65c5f9-f3f4-472e-9ed7-d90595144002` | 3 / 1.094134569 | 4 / 3.266362040 | 3 / 0.031498016 | - |
| 4 | ml_bias_variance_generalization | `c79ae468-500a-4b28-a0c9-7fc0a499e8c7` | 4 / 1.123289227 | - | 5 / 0.015625000 | - |
| 5 | ml_bias_variance_generalization | `238ddbf4-a7b9-4647-b485-79a96e6a48d5` | 5 / 1.132389069 | 3 / 3.755160404 | 4 / 0.031257631 | - |

#### bm25

| Rank | Document | Chunk UUID | Vector rank / distance | BM25 rank / score | RRF rank / score | Rerank score |
|---:|---|---|---|---|---|---:|
| 1 | ml_model_evaluation | `bd664c0a-5bcb-457d-b326-bddcb215638f` | 2 / 0.941775918 | 1 / 12.740429520 | 2 / 0.032522475 | - |
| 2 | ml_model_evaluation | `6d045457-927e-4d91-a801-80fb6b49a451` | 1 / 0.933049560 | 2 / 11.123085062 | 1 / 0.032522475 | - |
| 3 | ml_bias_variance_generalization | `238ddbf4-a7b9-4647-b485-79a96e6a48d5` | 5 / 1.132389069 | 3 / 3.755160404 | 4 / 0.031257631 | - |
| 4 | ml_bias_variance_generalization | `7e65c5f9-f3f4-472e-9ed7-d90595144002` | 3 / 1.094134569 | 4 / 3.266362040 | 3 / 0.031498016 | - |

#### hybrid

| Rank | Document | Chunk UUID | Vector rank / distance | BM25 rank / score | RRF rank / score | Rerank score |
|---:|---|---|---|---|---|---:|
| 1 | ml_model_evaluation | `6d045457-927e-4d91-a801-80fb6b49a451` | 1 / 0.933049560 | 2 / 11.123085062 | 1 / 0.032522475 | - |
| 2 | ml_model_evaluation | `bd664c0a-5bcb-457d-b326-bddcb215638f` | 2 / 0.941775918 | 1 / 12.740429520 | 2 / 0.032522475 | - |
| 3 | ml_bias_variance_generalization | `7e65c5f9-f3f4-472e-9ed7-d90595144002` | 3 / 1.094134569 | 4 / 3.266362040 | 3 / 0.031498016 | - |
| 4 | ml_bias_variance_generalization | `238ddbf4-a7b9-4647-b485-79a96e6a48d5` | 5 / 1.132389069 | 3 / 3.755160404 | 4 / 0.031257631 | - |
| 5 | ml_bias_variance_generalization | `c79ae468-500a-4b28-a0c9-7fc0a499e8c7` | 4 / 1.123289227 | - | 5 / 0.015625000 | - |

#### hybrid_reranked

| Rank | Document | Chunk UUID | Vector rank / distance | BM25 rank / score | RRF rank / score | Rerank score |
|---:|---|---|---|---|---|---:|
| 1 | ml_model_evaluation | `bd664c0a-5bcb-457d-b326-bddcb215638f` | 2 / 0.941775918 | 1 / 12.740429520 | 2 / 0.032522475 | 6.950 |
| 2 | ml_model_evaluation | `6d045457-927e-4d91-a801-80fb6b49a451` | 1 / 0.933049560 | 2 / 11.123085062 | 1 / 0.032522475 | 5.000 |
| 3 | ml_bias_variance_generalization | `7e65c5f9-f3f4-472e-9ed7-d90595144002` | 3 / 1.094134569 | 4 / 3.266362040 | 3 / 0.031498016 | 2.900 |
| 4 | ml_bias_variance_generalization | `238ddbf4-a7b9-4647-b485-79a96e6a48d5` | 5 / 1.132389069 | 3 / 3.755160404 | 4 / 0.031257631 | 2.850 |
| 5 | ml_overfitting_underfitting | `1a8573db-c271-4cd4-9bc8-097466513548` | 6 / 1.189512968 | - | 6 / 0.015151515 | 2.750 |

### Exact heuristic contributions for fused candidates

| Fused rank | Document/chunk | UUID | Matched query tokens (repetitions counted) | Overlap + rank bonus = score |
|---:|---|---|---|---|
| 1 | ml_model_evaluation/0 | `6d045457-927e-4d91-a801-80fb6b49a451` | can, accuracy, misleading, evaluation | 4.00 + 1.00 = 5.00 |
| 2 | ml_model_evaluation/1 | `bd664c0a-5bcb-457d-b326-bddcb215638f` | when, can, accuracy, misleading, evaluation, metric | 6.00 + 0.95 = 6.95 |
| 3 | ml_bias_variance_generalization/1 | `7e65c5f9-f3f4-472e-9ed7-d90595144002` | can, accuracy | 2.00 + 0.90 = 2.90 |
| 4 | ml_bias_variance_generalization/2 | `238ddbf4-a7b9-4647-b485-79a96e6a48d5` | can, accuracy | 2.00 + 0.85 = 2.85 |
| 5 | ml_bias_variance_generalization/0 | `c79ae468-500a-4b28-a0c9-7fc0a499e8c7` |  | 0.00 + 0.80 = 0.80 |
| 6 | ml_overfitting_underfitting/1 | `1a8573db-c271-4cd4-9bc8-097466513548` | when, can | 2.00 + 0.75 = 2.75 |
| 7 | ml_supervised_learning_basics/2 | `8e3c8941-518e-401e-961b-091b2c14a7cc` |  | 0.00 + 0.70 = 0.70 |
| 8 | ml_overfitting_underfitting/0 | `d7755e05-d3c6-4865-9453-7d9464895375` | when | 1.00 + 0.65 = 1.65 |
| 9 | ml_supervised_learning_basics/1 | `66277f9c-97b1-4aa9-885f-1a7cde13ffbe` | can | 1.00 + 0.60 = 1.60 |
| 10 | ml_classification_regression/0 | `a991caeb-71fd-45b3-8fb8-aa3b541b8f91` |  | 0.00 + 0.55 = 0.55 |

## retrieval_003

How do processes and threads differ in memory sharing and communication?

### Canonical evidence

**os_process_vs_thread / chunk 1 / `a4d8fe4d-300d-49b7-b7a9-c573f06af200`**

A process is an independent program in execution. Each process has its own memory space, resources, and execution state. A thread is the smallest unit of execution within a process. Threads that belong to the same process share the same memory space and resources, but each thread has its own stack and program counter. Processes are more isolated than threads. Because each process has its own memory space, communication between processes usually requires inter-process communication mechanisms such as pipes, sockets, or shared memory. Threads communicate more easily because they share memory. This makes threads more efficient for tasks that need frequent communication, but it also introduces risks such as race conditions and synchronization problems.


### Alternatives from annotation notes

Canonical evidence covers separate process memory, shared thread memory, IPC, and communication tradeoffs. Full equivalent evidence: 28a7c7fa-ee37-43be-a91c-7243ed15b0ac (os_process_vs_thread, chunk 2). Supporting alternatives covering the basic complete comparison: 0c277ad4-37e2-4378-ae31-64e52a11d86a (os_processes_threads_scheduling, chunk 0); 035326e9-1a04-4aed-9dc8-221befcf1945 (os_processes_threads_scheduling, chunk 1). Partial supporting evidence: dbd54f08-345e-4f7f-aa82-2ab6bde2c3c3 (os_process_vs_thread, chunk 0) covers memory sharing but not communication. Alternatives are excluded from automatic scoring.

**os_process_vs_thread / chunk 2 / `28a7c7fa-ee37-43be-a91c-7243ed15b0ac`**

Because each process has its own memory space, communication between processes usually requires inter-process communication mechanisms such as pipes, sockets, or shared memory. Threads communicate more easily because they share memory. This makes threads more efficient for tasks that need frequent communication, but it also introduces risks such as race conditions and synchronization problems. Creating and switching between processes is generally more expensive than creating and switching between threads because processes require more operating system overhead. Multithreading is useful for applications that perform multiple tasks concurrently, such as a web server handling multiple client requests or a program performing background work while keeping the user interface responsive. A process can contain one thread or multiple threads.

**os_processes_threads_scheduling / chunk 0 / `0c277ad4-37e2-4378-ae31-64e52a11d86a`**

A process is an executing program with its own memory space, resources, and execution state. A thread is a smaller unit of execution within a process. Threads of the same process share memory and resources, which makes communication between them faster but also introduces synchronization issues. Context switching between processes is generally more expensive than switching between threads because more state must be saved and restored.

**os_processes_threads_scheduling / chunk 1 / `035326e9-1a04-4aed-9dc8-221befcf1945`**

A process is an executing program with its own memory space, resources, and execution state. A thread is a smaller unit of execution within a process. Threads of the same process share memory and resources, which makes communication between them faster but also introduces synchronization issues. Context switching between processes is generally more expensive than switching between threads because more state must be saved and restored. CPU scheduling determines which ready process or thread gets access to the processor. Common scheduling algorithms include first-come first-served, shortest job first, priority scheduling, and round robin. First-come first-served is simple but can produce poor average waiting time. Round robin assigns each process a fixed time quantum and cycles through ready tasks, which improves responsiveness in time-sharing systems. Starvation can occur when lower-priority tasks wait indefinitely.

**os_process_vs_thread / chunk 0 / `dbd54f08-345e-4f7f-aa82-2ab6bde2c3c3`**

A process is an independent program in execution. Each process has its own memory space, resources, and execution state. A thread is the smallest unit of execution within a process. Threads that belong to the same process share the same memory space and resources, but each thread has its own stack and program counter. Processes are more isolated than threads.


### Ranking and score tables

Rank agreement with saved results: {'vector': True, 'bm25': True, 'hybrid': True, 'hybrid_reranked': True}

Reranker non-stopword question tokens: processes, threads, differ, memory, sharing, communication

#### vector

| Rank | Document | Chunk UUID | Vector rank / distance | BM25 rank / score | RRF rank / score | Rerank score |
|---:|---|---|---|---|---|---:|
| 1 | os_process_vs_thread | `28a7c7fa-ee37-43be-a91c-7243ed15b0ac` | 1 / 0.518799365 | 2 / 14.874629442 | 1 / 0.032522475 | - |
| 2 | os_process_vs_thread | `a4d8fe4d-300d-49b7-b7a9-c573f06af200` | 2 / 0.544055164 | 1 / 15.110589584 | 2 / 0.032522475 | - |
| 3 | os_processes_threads_scheduling | `0c277ad4-37e2-4378-ae31-64e52a11d86a` | 3 / 0.618420601 | 3 / 12.999244599 | 3 / 0.031746032 | - |
| 4 | os_processes_threads_scheduling | `035326e9-1a04-4aed-9dc8-221befcf1945` | 4 / 0.657351375 | 4 / 12.372184922 | 4 / 0.031250000 | - |
| 5 | os_process_vs_thread | `dbd54f08-345e-4f7f-aa82-2ab6bde2c3c3` | 5 / 0.661255956 | 5 / 10.316791364 | 5 / 0.030769231 | - |

#### bm25

| Rank | Document | Chunk UUID | Vector rank / distance | BM25 rank / score | RRF rank / score | Rerank score |
|---:|---|---|---|---|---|---:|
| 1 | os_process_vs_thread | `a4d8fe4d-300d-49b7-b7a9-c573f06af200` | 2 / 0.544055164 | 1 / 15.110589584 | 2 / 0.032522475 | - |
| 2 | os_process_vs_thread | `28a7c7fa-ee37-43be-a91c-7243ed15b0ac` | 1 / 0.518799365 | 2 / 14.874629442 | 1 / 0.032522475 | - |
| 3 | os_processes_threads_scheduling | `0c277ad4-37e2-4378-ae31-64e52a11d86a` | 3 / 0.618420601 | 3 / 12.999244599 | 3 / 0.031746032 | - |
| 4 | os_processes_threads_scheduling | `035326e9-1a04-4aed-9dc8-221befcf1945` | 4 / 0.657351375 | 4 / 12.372184922 | 4 / 0.031250000 | - |
| 5 | os_process_vs_thread | `dbd54f08-345e-4f7f-aa82-2ab6bde2c3c3` | 5 / 0.661255956 | 5 / 10.316791364 | 5 / 0.030769231 | - |

#### hybrid

| Rank | Document | Chunk UUID | Vector rank / distance | BM25 rank / score | RRF rank / score | Rerank score |
|---:|---|---|---|---|---|---:|
| 1 | os_process_vs_thread | `28a7c7fa-ee37-43be-a91c-7243ed15b0ac` | 1 / 0.518799365 | 2 / 14.874629442 | 1 / 0.032522475 | - |
| 2 | os_process_vs_thread | `a4d8fe4d-300d-49b7-b7a9-c573f06af200` | 2 / 0.544055164 | 1 / 15.110589584 | 2 / 0.032522475 | - |
| 3 | os_processes_threads_scheduling | `0c277ad4-37e2-4378-ae31-64e52a11d86a` | 3 / 0.618420601 | 3 / 12.999244599 | 3 / 0.031746032 | - |
| 4 | os_processes_threads_scheduling | `035326e9-1a04-4aed-9dc8-221befcf1945` | 4 / 0.657351375 | 4 / 12.372184922 | 4 / 0.031250000 | - |
| 5 | os_process_vs_thread | `dbd54f08-345e-4f7f-aa82-2ab6bde2c3c3` | 5 / 0.661255956 | 5 / 10.316791364 | 5 / 0.030769231 | - |

#### hybrid_reranked

| Rank | Document | Chunk UUID | Vector rank / distance | BM25 rank / score | RRF rank / score | Rerank score |
|---:|---|---|---|---|---|---:|
| 1 | os_processes_threads_scheduling | `035326e9-1a04-4aed-9dc8-221befcf1945` | 4 / 0.657351375 | 4 / 12.372184922 | 4 / 0.031250000 | 5.850 |
| 2 | os_process_vs_thread | `28a7c7fa-ee37-43be-a91c-7243ed15b0ac` | 1 / 0.518799365 | 2 / 14.874629442 | 1 / 0.032522475 | 5.000 |
| 3 | os_process_vs_thread | `a4d8fe4d-300d-49b7-b7a9-c573f06af200` | 2 / 0.544055164 | 1 / 15.110589584 | 2 / 0.032522475 | 4.950 |
| 4 | os_processes_threads_scheduling | `0c277ad4-37e2-4378-ae31-64e52a11d86a` | 3 / 0.618420601 | 3 / 12.999244599 | 3 / 0.031746032 | 4.900 |
| 5 | os_process_vs_thread | `dbd54f08-345e-4f7f-aa82-2ab6bde2c3c3` | 5 / 0.661255956 | 5 / 10.316791364 | 5 / 0.030769231 | 3.800 |

### Exact heuristic contributions for fused candidates

| Fused rank | Document/chunk | UUID | Matched query tokens (repetitions counted) | Overlap + rank bonus = score |
|---:|---|---|---|---|
| 1 | os_process_vs_thread/2 | `28a7c7fa-ee37-43be-a91c-7243ed15b0ac` | processes, threads, memory, communication | 4.00 + 1.00 = 5.00 |
| 2 | os_process_vs_thread/1 | `a4d8fe4d-300d-49b7-b7a9-c573f06af200` | processes, threads, memory, communication | 4.00 + 0.95 = 4.95 |
| 3 | os_processes_threads_scheduling/0 | `0c277ad4-37e2-4378-ae31-64e52a11d86a` | processes, threads, memory, communication | 4.00 + 0.90 = 4.90 |
| 4 | os_processes_threads_scheduling/1 | `035326e9-1a04-4aed-9dc8-221befcf1945` | processes, threads, memory, sharing, communication | 5.00 + 0.85 = 5.85 |
| 5 | os_process_vs_thread/0 | `dbd54f08-345e-4f7f-aa82-2ab6bde2c3c3` | processes, threads, memory | 3.00 + 0.80 = 3.80 |
| 6 | os_process_vs_thread/3 | `fddc7e74-63c8-4d3b-b343-a3aa1d8d7987` | processes, threads | 2.00 + 0.75 = 2.75 |
| 7 | os_processes_threads_scheduling/2 | `5c0117ef-6ce2-4d21-b39b-adc2586cdaa6` | sharing | 1.00 + 0.70 = 1.70 |
| 8 | ml_model_evaluation/1 | `bd664c0a-5bcb-457d-b326-bddcb215638f` |  | 0.00 + 0.65 = 0.65 |
| 9 | db_transactions_concurrency/2 | `b2b2b736-dbec-45ae-b811-77d5a03d785e` |  | 0.00 + 0.60 = 0.60 |
| 10 | ml_model_evaluation/0 | `6d045457-927e-4d91-a801-80fb6b49a451` |  | 0.00 + 0.55 = 0.55 |
| 11 | db_transactions_concurrency/1 | `ece01229-7d42-455a-a3e2-cf789c5dae2c` |  | 0.00 + 0.50 = 0.50 |
| 12 | db_transactions_concurrency/0 | `0dd5a5bf-5dab-4d48-b5f3-566ff4b80281` |  | 0.00 + 0.45 = 0.45 |
| 13 | ml_bias_variance_generalization/2 | `238ddbf4-a7b9-4647-b485-79a96e6a48d5` |  | 0.00 + 0.40 = 0.40 |

## retrieval_008

How does partial dependency differ from transitive dependency, and which normal form removes each?

### Canonical evidence

**db_normalization_intro / chunk 2 / `73c987b6-90bc-41e1-bbb7-12bc713de952`**

A deletion anomaly happens when removing one row accidentally removes other valuable information. The first normal form requires that each attribute contain atomic values and that there are no repeating groups. The second normal form removes partial dependency, meaning that non-key attributes must depend on the whole primary key rather than just part of a composite key. The third normal form removes transitive dependency, so non-key attributes should not depend on other non-key attributes. For example, if a student table stores department_name and department_office, and department_office depends on department_name rather than student_id, then the design has a transitive dependency. Decomposition is often used to split such a table into smaller relations while preserving data meaning.


### Alternatives from annotation notes

Canonical evidence contains both definitions, normal-form assignments, and a concrete example. Full equivalent evidence: f47f5e9c-59a3-4859-8580-c16ffb34ed60 (db_normalization_intro, chunk 1) supplies the same requested definitions and assignments.

**db_normalization_intro / chunk 1 / `f47f5e9c-59a3-4859-8580-c16ffb34ed60`**

Normalization is the process of organizing data in a relational database to reduce redundancy and improve data integrity. Poorly designed tables often repeat the same facts in multiple rows, which can cause update anomalies, insertion anomalies, and deletion anomalies. An update anomaly happens when the same fact must be changed in several places and some copies are missed. An insertion anomaly happens when a new fact cannot be inserted without adding unrelated data. A deletion anomaly happens when removing one row accidentally removes other valuable information. The first normal form requires that each attribute contain atomic values and that there are no repeating groups. The second normal form removes partial dependency, meaning that non-key attributes must depend on the whole primary key rather than just part of a composite key. The third normal form removes transitive dependency, so non-key attributes should not depend on other non-key attributes.


### Ranking and score tables

Rank agreement with saved results: {'vector': True, 'bm25': True, 'hybrid': True, 'hybrid_reranked': True}

Reranker non-stopword question tokens: partial, dependency, differ, transitive, dependency, which, normal, form, removes, each

#### vector

| Rank | Document | Chunk UUID | Vector rank / distance | BM25 rank / score | RRF rank / score | Rerank score |
|---:|---|---|---|---|---|---:|
| 1 | db_normalization_intro | `73c987b6-90bc-41e1-bbb7-12bc713de952` | 1 / 0.746458411 | 1 / 27.436240753 | 1 / 0.032786885 | - |
| 2 | db_normalization_intro | `f47f5e9c-59a3-4859-8580-c16ffb34ed60` | 2 / 1.072013021 | 2 / 25.518998187 | 2 / 0.032258065 | - |
| 3 | db_normalization_intro | `a1cbb9b1-26d3-4a25-a6db-73d26dc8eb68` | 3 / 1.395329237 | - | 5 / 0.015873016 | - |
| 4 | db_transactions_concurrency | `0dd5a5bf-5dab-4d48-b5f3-566ff4b80281` | 4 / 1.497480392 | - | 6 / 0.015625000 | - |
| 5 | db_transactions_concurrency | `ece01229-7d42-455a-a3e2-cf789c5dae2c` | 5 / 1.506222963 | - | 8 / 0.015384615 | - |

#### bm25

| Rank | Document | Chunk UUID | Vector rank / distance | BM25 rank / score | RRF rank / score | Rerank score |
|---:|---|---|---|---|---|---:|
| 1 | db_normalization_intro | `73c987b6-90bc-41e1-bbb7-12bc713de952` | 1 / 0.746458411 | 1 / 27.436240753 | 1 / 0.032786885 | - |
| 2 | db_normalization_intro | `f47f5e9c-59a3-4859-8580-c16ffb34ed60` | 2 / 1.072013021 | 2 / 25.518998187 | 2 / 0.032258065 | - |
| 3 | ml_supervised_learning_basics | `3ccba452-0e10-40ef-ade4-06a09c80b66c` | 7 / 1.589658976 | 3 / 4.702662708 | 3 / 0.030798389 | - |
| 4 | os_processes_threads_scheduling | `5c0117ef-6ce2-4d21-b39b-adc2586cdaa6` | - | 4 / 4.600540513 | 7 / 0.015625000 | - |
| 5 | os_processes_threads_scheduling | `035326e9-1a04-4aed-9dc8-221befcf1945` | - | 5 / 4.519504218 | 9 / 0.015384615 | - |

#### hybrid

| Rank | Document | Chunk UUID | Vector rank / distance | BM25 rank / score | RRF rank / score | Rerank score |
|---:|---|---|---|---|---|---:|
| 1 | db_normalization_intro | `73c987b6-90bc-41e1-bbb7-12bc713de952` | 1 / 0.746458411 | 1 / 27.436240753 | 1 / 0.032786885 | - |
| 2 | db_normalization_intro | `f47f5e9c-59a3-4859-8580-c16ffb34ed60` | 2 / 1.072013021 | 2 / 25.518998187 | 2 / 0.032258065 | - |
| 3 | ml_supervised_learning_basics | `3ccba452-0e10-40ef-ade4-06a09c80b66c` | 7 / 1.589658976 | 3 / 4.702662708 | 3 / 0.030798389 | - |
| 4 | ml_supervised_learning_basics | `66277f9c-97b1-4aa9-885f-1a7cde13ffbe` | 6 / 1.557403564 | 10 / 3.466058608 | 4 / 0.029437229 | - |
| 5 | db_normalization_intro | `a1cbb9b1-26d3-4a25-a6db-73d26dc8eb68` | 3 / 1.395329237 | - | 5 / 0.015873016 | - |

#### hybrid_reranked

| Rank | Document | Chunk UUID | Vector rank / distance | BM25 rank / score | RRF rank / score | Rerank score |
|---:|---|---|---|---|---|---:|
| 1 | db_normalization_intro | `f47f5e9c-59a3-4859-8580-c16ffb34ed60` | 2 / 1.072013021 | 2 / 25.518998187 | 2 / 0.032258065 | 9.950 |
| 2 | db_normalization_intro | `73c987b6-90bc-41e1-bbb7-12bc713de952` | 1 / 0.746458411 | 1 / 27.436240753 | 1 / 0.032786885 | 9.000 |
| 3 | ml_supervised_learning_basics | `3ccba452-0e10-40ef-ade4-06a09c80b66c` | 7 / 1.589658976 | 3 / 4.702662708 | 3 / 0.030798389 | 2.900 |
| 4 | ml_supervised_learning_basics | `66277f9c-97b1-4aa9-885f-1a7cde13ffbe` | 6 / 1.557403564 | 10 / 3.466058608 | 4 / 0.029437229 | 2.850 |
| 5 | os_processes_threads_scheduling | `5c0117ef-6ce2-4d21-b39b-adc2586cdaa6` | - | 4 / 4.600540513 | 7 / 0.015625000 | 2.700 |

### Exact heuristic contributions for fused candidates

| Fused rank | Document/chunk | UUID | Matched query tokens (repetitions counted) | Overlap + rank bonus = score |
|---:|---|---|---|---|
| 1 | db_normalization_intro/2 | `73c987b6-90bc-41e1-bbb7-12bc713de952` | partial, dependency, transitive, dependency, normal, form, removes, each | 8.00 + 1.00 = 9.00 |
| 2 | db_normalization_intro/1 | `f47f5e9c-59a3-4859-8580-c16ffb34ed60` | partial, dependency, transitive, dependency, which, normal, form, removes, each | 9.00 + 0.95 = 9.95 |
| 3 | ml_supervised_learning_basics/0 | `3ccba452-0e10-40ef-ade4-06a09c80b66c` | which, each | 2.00 + 0.90 = 2.90 |
| 4 | ml_supervised_learning_basics/1 | `66277f9c-97b1-4aa9-885f-1a7cde13ffbe` | which, each | 2.00 + 0.85 = 2.85 |
| 5 | db_normalization_intro/0 | `a1cbb9b1-26d3-4a25-a6db-73d26dc8eb68` | which | 1.00 + 0.80 = 1.80 |
| 6 | db_transactions_concurrency/0 | `0dd5a5bf-5dab-4d48-b5f3-566ff4b80281` |  | 0.00 + 0.75 = 0.75 |
| 7 | os_processes_threads_scheduling/2 | `5c0117ef-6ce2-4d21-b39b-adc2586cdaa6` | which, each | 2.00 + 0.70 = 2.70 |
| 8 | db_transactions_concurrency/1 | `ece01229-7d42-455a-a3e2-cf789c5dae2c` |  | 0.00 + 0.65 = 0.65 |
| 9 | os_processes_threads_scheduling/1 | `035326e9-1a04-4aed-9dc8-221befcf1945` | which, each | 2.00 + 0.60 = 2.60 |
| 10 | ml_bias_variance_generalization/2 | `238ddbf4-a7b9-4647-b485-79a96e6a48d5` | each | 1.00 + 0.55 = 1.55 |
| 11 | ml_model_evaluation/1 | `bd664c0a-5bcb-457d-b326-bddcb215638f` |  | 0.00 + 0.50 = 0.50 |
| 12 | ml_overfitting_underfitting/1 | `1a8573db-c271-4cd4-9bc8-097466513548` |  | 0.00 + 0.45 = 0.45 |
| 13 | ml_model_evaluation/0 | `6d045457-927e-4d91-a801-80fb6b49a451` |  | 0.00 + 0.40 = 0.40 |
| 14 | ml_classification_regression/0 | `a991caeb-71fd-45b3-8fb8-aa3b541b8f91` |  | 0.00 + 0.35 = 0.35 |
| 15 | ml_bias_variance_generalization/1 | `7e65c5f9-f3f4-472e-9ed7-d90595144002` | each | 1.00 + 0.30 = 1.30 |
| 16 | ml_overfitting_underfitting/0 | `d7755e05-d3c6-4865-9453-7d9464895375` |  | 0.00 + 0.25 = 0.25 |

## retrieval_009

Which database guarantee means that an accepted change survives even if the machine fails afterward?

### Canonical evidence

**db_transactions_concurrency / chunk 2 / `b2b2b736-dbec-45ae-b811-77d5a03d785e`**

Durability means that once a transaction is committed, its effects persist even after a crash. Concurrency control is needed because many users may access the same data at the same time. Problems that can appear without proper control include lost updates, dirty reads, and non-repeatable reads. A lost update occurs when one transaction overwrites the result of another. A dirty read happens when a transaction reads data written by another transaction that has not yet committed. A non-repeatable read occurs when the same query returns different results within a single transaction because another transaction modified the data in the meantime. Locking and multiversion concurrency control are two common approaches to handling concurrency.


### Alternatives from annotation notes

Semantic paraphrase of durability; canonical evidence explicitly states persistence after commit and crash. Full equivalent evidence: ece01229-7d42-455a-a3e2-cf789c5dae2c (db_transactions_concurrency, chunk 1) repeats the durability definition.

**db_transactions_concurrency / chunk 1 / `ece01229-7d42-455a-a3e2-cf789c5dae2c`**

A transaction is a logical unit of work that must either complete entirely or have no effect at all. The ACID properties describe the reliability of transactions. Atomicity means all operations of a transaction happen or none happen. Consistency means the database moves from one valid state to another valid state. Isolation means concurrent transactions should not interfere in a way that produces incorrect results. Durability means that once a transaction is committed, its effects persist even after a crash. Concurrency control is needed because many users may access the same data at the same time. Problems that can appear without proper control include lost updates, dirty reads, and non-repeatable reads. A lost update occurs when one transaction overwrites the result of another. A dirty read happens when a transaction reads data written by another transaction that has not yet committed.


### Ranking and score tables

Rank agreement with saved results: {'vector': True, 'bm25': True, 'hybrid': True, 'hybrid_reranked': True}

Reranker non-stopword question tokens: which, database, guarantee, means, accepted, change, survives, even, if, machine, fails, afterward

#### vector

| Rank | Document | Chunk UUID | Vector rank / distance | BM25 rank / score | RRF rank / score | Rerank score |
|---:|---|---|---|---|---|---:|
| 1 | db_transactions_concurrency | `b2b2b736-dbec-45ae-b811-77d5a03d785e` | 1 / 0.935209095 | 5 / 5.288697047 | 3 / 0.031778058 | - |
| 2 | db_transactions_concurrency | `ece01229-7d42-455a-a3e2-cf789c5dae2c` | 2 / 1.129172683 | 1 / 9.228671391 | 1 / 0.032522475 | - |
| 3 | db_transactions_concurrency | `0dd5a5bf-5dab-4d48-b5f3-566ff4b80281` | 3 / 1.255564928 | 2 / 8.195374366 | 2 / 0.032002048 | - |
| 4 | db_normalization_intro | `f47f5e9c-59a3-4859-8580-c16ffb34ed60` | 4 / 1.278962493 | 7 / 3.950304033 | 5 / 0.030550373 | - |
| 5 | db_normalization_intro | `a1cbb9b1-26d3-4a25-a6db-73d26dc8eb68` | 5 / 1.286458969 | 4 / 5.553700760 | 4 / 0.031009615 | - |

#### bm25

| Rank | Document | Chunk UUID | Vector rank / distance | BM25 rank / score | RRF rank / score | Rerank score |
|---:|---|---|---|---|---|---:|
| 1 | db_transactions_concurrency | `ece01229-7d42-455a-a3e2-cf789c5dae2c` | 2 / 1.129172683 | 1 / 9.228671391 | 1 / 0.032522475 | - |
| 2 | db_transactions_concurrency | `0dd5a5bf-5dab-4d48-b5f3-566ff4b80281` | 3 / 1.255564928 | 2 / 8.195374366 | 2 / 0.032002048 | - |
| 3 | ml_supervised_learning_basics | `66277f9c-97b1-4aa9-885f-1a7cde13ffbe` | - | 3 / 6.039837682 | 8 / 0.015873016 | - |
| 4 | db_normalization_intro | `a1cbb9b1-26d3-4a25-a6db-73d26dc8eb68` | 5 / 1.286458969 | 4 / 5.553700760 | 4 / 0.031009615 | - |
| 5 | db_transactions_concurrency | `b2b2b736-dbec-45ae-b811-77d5a03d785e` | 1 / 0.935209095 | 5 / 5.288697047 | 3 / 0.031778058 | - |

#### hybrid

| Rank | Document | Chunk UUID | Vector rank / distance | BM25 rank / score | RRF rank / score | Rerank score |
|---:|---|---|---|---|---|---:|
| 1 | db_transactions_concurrency | `ece01229-7d42-455a-a3e2-cf789c5dae2c` | 2 / 1.129172683 | 1 / 9.228671391 | 1 / 0.032522475 | - |
| 2 | db_transactions_concurrency | `0dd5a5bf-5dab-4d48-b5f3-566ff4b80281` | 3 / 1.255564928 | 2 / 8.195374366 | 2 / 0.032002048 | - |
| 3 | db_transactions_concurrency | `b2b2b736-dbec-45ae-b811-77d5a03d785e` | 1 / 0.935209095 | 5 / 5.288697047 | 3 / 0.031778058 | - |
| 4 | db_normalization_intro | `a1cbb9b1-26d3-4a25-a6db-73d26dc8eb68` | 5 / 1.286458969 | 4 / 5.553700760 | 4 / 0.031009615 | - |
| 5 | db_normalization_intro | `f47f5e9c-59a3-4859-8580-c16ffb34ed60` | 4 / 1.278962493 | 7 / 3.950304033 | 5 / 0.030550373 | - |

#### hybrid_reranked

| Rank | Document | Chunk UUID | Vector rank / distance | BM25 rank / score | RRF rank / score | Rerank score |
|---:|---|---|---|---|---|---:|
| 1 | db_transactions_concurrency | `ece01229-7d42-455a-a3e2-cf789c5dae2c` | 2 / 1.129172683 | 1 / 9.228671391 | 1 / 0.032522475 | 4.000 |
| 2 | ml_supervised_learning_basics | `66277f9c-97b1-4aa9-885f-1a7cde13ffbe` | - | 3 / 6.039837682 | 8 / 0.015873016 | 3.650 |
| 3 | db_transactions_concurrency | `0dd5a5bf-5dab-4d48-b5f3-566ff4b80281` | 3 / 1.255564928 | 2 / 8.195374366 | 2 / 0.032002048 | 2.950 |
| 4 | db_transactions_concurrency | `b2b2b736-dbec-45ae-b811-77d5a03d785e` | 1 / 0.935209095 | 5 / 5.288697047 | 3 / 0.031778058 | 2.900 |
| 5 | db_normalization_intro | `a1cbb9b1-26d3-4a25-a6db-73d26dc8eb68` | 5 / 1.286458969 | 4 / 5.553700760 | 4 / 0.031009615 | 2.850 |

### Exact heuristic contributions for fused candidates

| Fused rank | Document/chunk | UUID | Matched query tokens (repetitions counted) | Overlap + rank bonus = score |
|---:|---|---|---|---|
| 1 | db_transactions_concurrency/1 | `ece01229-7d42-455a-a3e2-cf789c5dae2c` | database, means, even | 3.00 + 1.00 = 4.00 |
| 2 | db_transactions_concurrency/0 | `0dd5a5bf-5dab-4d48-b5f3-566ff4b80281` | database, means | 2.00 + 0.95 = 2.95 |
| 3 | db_transactions_concurrency/2 | `b2b2b736-dbec-45ae-b811-77d5a03d785e` | means, even | 2.00 + 0.90 = 2.90 |
| 4 | db_normalization_intro/0 | `a1cbb9b1-26d3-4a25-a6db-73d26dc8eb68` | which, database | 2.00 + 0.85 = 2.85 |
| 5 | db_normalization_intro/1 | `f47f5e9c-59a3-4859-8580-c16ffb34ed60` | which, database | 2.00 + 0.80 = 2.80 |
| 6 | os_processes_threads_scheduling/2 | `5c0117ef-6ce2-4d21-b39b-adc2586cdaa6` | which | 1.00 + 0.75 = 1.75 |
| 7 | ml_supervised_learning_basics/2 | `8e3c8941-518e-401e-961b-091b2c14a7cc` | even | 1.00 + 0.70 = 1.70 |
| 8 | ml_supervised_learning_basics/1 | `66277f9c-97b1-4aa9-885f-1a7cde13ffbe` | which, even, machine | 3.00 + 0.65 = 3.65 |
| 9 | db_normalization_intro/2 | `73c987b6-90bc-41e1-bbb7-12bc713de952` | if | 1.00 + 0.60 = 1.60 |
| 10 | ml_supervised_learning_basics/0 | `3ccba452-0e10-40ef-ade4-06a09c80b66c` | which, machine | 2.00 + 0.55 = 2.55 |
| 11 | ml_bias_variance_generalization/2 | `238ddbf4-a7b9-4647-b485-79a96e6a48d5` |  | 0.00 + 0.50 = 0.50 |
| 12 | os_processes_threads_scheduling/1 | `035326e9-1a04-4aed-9dc8-221befcf1945` | which | 1.00 + 0.45 = 1.45 |
| 13 | ml_bias_variance_generalization/1 | `7e65c5f9-f3f4-472e-9ed7-d90595144002` | machine | 1.00 + 0.40 = 1.40 |

## retrieval_010

Inside one database operation, I ask for the same information twice and get different answers because someone else changed it. What problem is this?

### Canonical evidence

**db_transactions_concurrency / chunk 2 / `b2b2b736-dbec-45ae-b811-77d5a03d785e`**

Durability means that once a transaction is committed, its effects persist even after a crash. Concurrency control is needed because many users may access the same data at the same time. Problems that can appear without proper control include lost updates, dirty reads, and non-repeatable reads. A lost update occurs when one transaction overwrites the result of another. A dirty read happens when a transaction reads data written by another transaction that has not yet committed. A non-repeatable read occurs when the same query returns different results within a single transaction because another transaction modified the data in the meantime. Locking and multiversion concurrency control are two common approaches to handling concurrency.


### Alternatives from annotation notes

Semantic paraphrase of a non-repeatable read. Only the canonical chunk provides the complete definition; no full equivalent evidence is identified.

No alternatives recorded.

### Ranking and score tables

Rank agreement with saved results: {'vector': True, 'bm25': True, 'hybrid': True, 'hybrid_reranked': True}

Reranker non-stopword question tokens: inside, one, database, operation, i, ask, same, information, twice, get, different, answers, because, someone, else, changed, problem

#### vector

| Rank | Document | Chunk UUID | Vector rank / distance | BM25 rank / score | RRF rank / score | Rerank score |
|---:|---|---|---|---|---|---:|
| 1 | db_normalization_intro | `a1cbb9b1-26d3-4a25-a6db-73d26dc8eb68` | 1 / 1.122325659 | 3 / 9.810408224 | 1 / 0.032266458 | - |
| 2 | db_normalization_intro | `f47f5e9c-59a3-4859-8580-c16ffb34ed60` | 2 / 1.184072733 | 2 / 11.398852438 | 3 / 0.032258065 | - |
| 3 | db_transactions_concurrency | `b2b2b736-dbec-45ae-b811-77d5a03d785e` | 3 / 1.209409237 | 1 / 11.473729778 | 2 / 0.032266458 | - |
| 4 | db_transactions_concurrency | `ece01229-7d42-455a-a3e2-cf789c5dae2c` | 4 / 1.283786058 | 4 / 9.290355512 | 4 / 0.031250000 | - |
| 5 | db_normalization_intro | `73c987b6-90bc-41e1-bbb7-12bc713de952` | 5 / 1.405143023 | 10 / 4.631626242 | 6 / 0.029670330 | - |

#### bm25

| Rank | Document | Chunk UUID | Vector rank / distance | BM25 rank / score | RRF rank / score | Rerank score |
|---:|---|---|---|---|---|---:|
| 1 | db_transactions_concurrency | `b2b2b736-dbec-45ae-b811-77d5a03d785e` | 3 / 1.209409237 | 1 / 11.473729778 | 2 / 0.032266458 | - |
| 2 | db_normalization_intro | `f47f5e9c-59a3-4859-8580-c16ffb34ed60` | 2 / 1.184072733 | 2 / 11.398852438 | 3 / 0.032258065 | - |
| 3 | db_normalization_intro | `a1cbb9b1-26d3-4a25-a6db-73d26dc8eb68` | 1 / 1.122325659 | 3 / 9.810408224 | 1 / 0.032266458 | - |
| 4 | db_transactions_concurrency | `ece01229-7d42-455a-a3e2-cf789c5dae2c` | 4 / 1.283786058 | 4 / 9.290355512 | 4 / 0.031250000 | - |
| 5 | db_transactions_concurrency | `0dd5a5bf-5dab-4d48-b5f3-566ff4b80281` | 6 / 1.417225599 | 5 / 5.559394961 | 5 / 0.030536131 | - |

#### hybrid

| Rank | Document | Chunk UUID | Vector rank / distance | BM25 rank / score | RRF rank / score | Rerank score |
|---:|---|---|---|---|---|---:|
| 1 | db_normalization_intro | `a1cbb9b1-26d3-4a25-a6db-73d26dc8eb68` | 1 / 1.122325659 | 3 / 9.810408224 | 1 / 0.032266458 | - |
| 2 | db_transactions_concurrency | `b2b2b736-dbec-45ae-b811-77d5a03d785e` | 3 / 1.209409237 | 1 / 11.473729778 | 2 / 0.032266458 | - |
| 3 | db_normalization_intro | `f47f5e9c-59a3-4859-8580-c16ffb34ed60` | 2 / 1.184072733 | 2 / 11.398852438 | 3 / 0.032258065 | - |
| 4 | db_transactions_concurrency | `ece01229-7d42-455a-a3e2-cf789c5dae2c` | 4 / 1.283786058 | 4 / 9.290355512 | 4 / 0.031250000 | - |
| 5 | db_transactions_concurrency | `0dd5a5bf-5dab-4d48-b5f3-566ff4b80281` | 6 / 1.417225599 | 5 / 5.559394961 | 5 / 0.030536131 | - |

#### hybrid_reranked

| Rank | Document | Chunk UUID | Vector rank / distance | BM25 rank / score | RRF rank / score | Rerank score |
|---:|---|---|---|---|---|---:|
| 1 | db_normalization_intro | `f47f5e9c-59a3-4859-8580-c16ffb34ed60` | 2 / 1.184072733 | 2 / 11.398852438 | 3 / 0.032258065 | 5.900 |
| 2 | db_transactions_concurrency | `b2b2b736-dbec-45ae-b811-77d5a03d785e` | 3 / 1.209409237 | 1 / 11.473729778 | 2 / 0.032266458 | 4.950 |
| 3 | db_transactions_concurrency | `ece01229-7d42-455a-a3e2-cf789c5dae2c` | 4 / 1.283786058 | 4 / 9.290355512 | 4 / 0.031250000 | 4.850 |
| 4 | db_normalization_intro | `a1cbb9b1-26d3-4a25-a6db-73d26dc8eb68` | 1 / 1.122325659 | 3 / 9.810408224 | 1 / 0.032266458 | 4.000 |
| 5 | db_transactions_concurrency | `0dd5a5bf-5dab-4d48-b5f3-566ff4b80281` | 6 / 1.417225599 | 5 / 5.559394961 | 5 / 0.030536131 | 2.800 |

### Exact heuristic contributions for fused candidates

| Fused rank | Document/chunk | UUID | Matched query tokens (repetitions counted) | Overlap + rank bonus = score |
|---:|---|---|---|---|
| 1 | db_normalization_intro/0 | `a1cbb9b1-26d3-4a25-a6db-73d26dc8eb68` | database, same, changed | 3.00 + 1.00 = 4.00 |
| 2 | db_transactions_concurrency/2 | `b2b2b736-dbec-45ae-b811-77d5a03d785e` | one, same, different, because | 4.00 + 0.95 = 4.95 |
| 3 | db_normalization_intro/1 | `f47f5e9c-59a3-4859-8580-c16ffb34ed60` | one, database, same, information, changed | 5.00 + 0.90 = 5.90 |
| 4 | db_transactions_concurrency/1 | `ece01229-7d42-455a-a3e2-cf789c5dae2c` | one, database, same, because | 4.00 + 0.85 = 4.85 |
| 5 | db_transactions_concurrency/0 | `0dd5a5bf-5dab-4d48-b5f3-566ff4b80281` | one, database | 2.00 + 0.80 = 2.80 |
| 6 | db_normalization_intro/2 | `73c987b6-90bc-41e1-bbb7-12bc713de952` | one, information | 2.00 + 0.75 = 2.75 |
| 7 | os_process_vs_thread/2 | `28a7c7fa-ee37-43be-a91c-7243ed15b0ac` | one, because | 2.00 + 0.70 = 2.70 |
| 8 | os_process_vs_thread/1 | `a4d8fe4d-300d-49b7-b7a9-c573f06af200` | same, because | 2.00 + 0.65 = 2.65 |
| 9 | ml_bias_variance_generalization/1 | `7e65c5f9-f3f4-472e-9ed7-d90595144002` | one | 1.00 + 0.60 = 1.60 |
| 10 | ml_bias_variance_generalization/0 | `c79ae468-500a-4b28-a0c9-7fc0a499e8c7` |  | 0.00 + 0.55 = 0.55 |
| 11 | os_process_vs_thread/3 | `fddc7e74-63c8-4d3b-b343-a3aa1d8d7987` | one, because | 2.00 + 0.50 = 2.50 |
| 12 | os_processes_threads_scheduling/0 | `0c277ad4-37e2-4378-ae31-64e52a11d86a` | same, because | 2.00 + 0.45 = 2.45 |
| 13 | ml_bias_variance_generalization/2 | `238ddbf4-a7b9-4647-b485-79a96e6a48d5` | one | 1.00 + 0.40 = 1.40 |

## retrieval_011

Would predicting whether a message is junk and predicting a property's sale price use the same kind of supervised-learning task? Explain the distinction.

### Canonical evidence

**ml_classification_regression / chunk 0 / `a991caeb-71fd-45b3-8fb8-aa3b541b8f91`**

Classification predicts discrete categories. Examples include spam detection, disease diagnosis, and sentiment analysis. Regression predicts continuous numerical values. Examples include house price prediction and temperature forecasting. Classification and regression are the two main categories of supervised learning problems. The choice between classification and regression depends on the type of target variable.


### Alternatives from annotation notes

Canonical evidence gives both task definitions and spam/house-price examples. Full equivalent evidence: 66277f9c-97b1-4aa9-885f-1a7cde13ffbe (ml_supervised_learning_basics, chunk 1) supports both parts. Partial supporting evidence: 3ccba452-0e10-40ef-ade4-06a09c80b66c (ml_supervised_learning_basics, chunk 0) supports classification; 8e3c8941-518e-401e-961b-091b2c14a7cc (ml_supervised_learning_basics, chunk 2) supports regression.

**ml_supervised_learning_basics / chunk 1 / `66277f9c-97b1-4aa9-885f-1a7cde13ffbe`**

Supervised learning is a machine learning paradigm in which a model learns from labeled examples. Each training example contains input features and a target output. The goal is to learn a mapping from inputs to outputs so that the model can generalize to unseen data. Supervised learning tasks are often divided into classification and regression. Classification predicts discrete categories, such as whether an email is spam or not spam. Regression predicts continuous values, such as the price of a house. During training, the model minimizes a loss function that measures the difference between predictions and true labels. Training error refers to performance on the training set, while test error refers to performance on new unseen data. A model that performs very well on training data but poorly on test data is said to be overfitting. A model that performs poorly even on training data may be underfitting.

**ml_supervised_learning_basics / chunk 0 / `3ccba452-0e10-40ef-ade4-06a09c80b66c`**

Supervised learning is a machine learning paradigm in which a model learns from labeled examples. Each training example contains input features and a target output. The goal is to learn a mapping from inputs to outputs so that the model can generalize to unseen data. Supervised learning tasks are often divided into classification and regression. Classification predicts discrete categories, such as whether an email is spam or not spam.

**ml_supervised_learning_basics / chunk 2 / `8e3c8941-518e-401e-961b-091b2c14a7cc`**

Regression predicts continuous values, such as the price of a house. During training, the model minimizes a loss function that measures the difference between predictions and true labels. Training error refers to performance on the training set, while test error refers to performance on new unseen data. A model that performs very well on training data but poorly on test data is said to be overfitting. A model that performs poorly even on training data may be underfitting. Feature selection, regularization, and cross-validation are common techniques used to improve generalization.


### Ranking and score tables

Rank agreement with saved results: {'vector': True, 'bm25': True, 'hybrid': True, 'hybrid_reranked': True}

Reranker non-stopword question tokens: would, predicting, whether, message, junk, predicting, property, s, sale, price, use, same, kind, supervised, learning, task, explain, distinction

#### vector

| Rank | Document | Chunk UUID | Vector rank / distance | BM25 rank / score | RRF rank / score | Rerank score |
|---:|---|---|---|---|---|---:|
| 1 | ml_classification_regression | `a991caeb-71fd-45b3-8fb8-aa3b541b8f91` | 1 / 0.843102694 | 3 / 9.480320325 | 2 / 0.032266458 | - |
| 2 | ml_supervised_learning_basics | `66277f9c-97b1-4aa9-885f-1a7cde13ffbe` | 2 / 0.978721738 | 1 / 11.782393076 | 1 / 0.032522475 | - |
| 3 | ml_supervised_learning_basics | `3ccba452-0e10-40ef-ade4-06a09c80b66c` | 3 / 1.013628840 | 2 / 11.572153672 | 3 / 0.032002048 | - |
| 4 | ml_supervised_learning_basics | `8e3c8941-518e-401e-961b-091b2c14a7cc` | 4 / 1.076189280 | - | 6 / 0.015625000 | - |
| 5 | ml_model_evaluation | `6d045457-927e-4d91-a801-80fb6b49a451` | 5 / 1.250681520 | - | 8 / 0.015384615 | - |

#### bm25

| Rank | Document | Chunk UUID | Vector rank / distance | BM25 rank / score | RRF rank / score | Rerank score |
|---:|---|---|---|---|---|---:|
| 1 | ml_supervised_learning_basics | `66277f9c-97b1-4aa9-885f-1a7cde13ffbe` | 2 / 0.978721738 | 1 / 11.782393076 | 1 / 0.032522475 | - |
| 2 | ml_supervised_learning_basics | `3ccba452-0e10-40ef-ade4-06a09c80b66c` | 3 / 1.013628840 | 2 / 11.572153672 | 3 / 0.032002048 | - |
| 3 | ml_classification_regression | `a991caeb-71fd-45b3-8fb8-aa3b541b8f91` | 1 / 0.843102694 | 3 / 9.480320325 | 2 / 0.032266458 | - |
| 4 | ml | `e3380555-fb30-454c-9a43-f8e3d66c05b9` | - | 4 / 6.948877511 | 7 / 0.015625000 | - |
| 5 | ml_bias_variance_generalization | `c79ae468-500a-4b28-a0c9-7fc0a499e8c7` | 7 / 1.292668819 | 5 / 6.402738419 | 4 / 0.030309989 | - |

#### hybrid

| Rank | Document | Chunk UUID | Vector rank / distance | BM25 rank / score | RRF rank / score | Rerank score |
|---:|---|---|---|---|---|---:|
| 1 | ml_supervised_learning_basics | `66277f9c-97b1-4aa9-885f-1a7cde13ffbe` | 2 / 0.978721738 | 1 / 11.782393076 | 1 / 0.032522475 | - |
| 2 | ml_classification_regression | `a991caeb-71fd-45b3-8fb8-aa3b541b8f91` | 1 / 0.843102694 | 3 / 9.480320325 | 2 / 0.032266458 | - |
| 3 | ml_supervised_learning_basics | `3ccba452-0e10-40ef-ade4-06a09c80b66c` | 3 / 1.013628840 | 2 / 11.572153672 | 3 / 0.032002048 | - |
| 4 | ml_bias_variance_generalization | `c79ae468-500a-4b28-a0c9-7fc0a499e8c7` | 7 / 1.292668819 | 5 / 6.402738419 | 4 / 0.030309989 | - |
| 5 | ml_bias_variance_generalization | `7e65c5f9-f3f4-472e-9ed7-d90595144002` | 8 / 1.308321357 | 6 / 4.987128914 | 5 / 0.029857398 | - |

#### hybrid_reranked

| Rank | Document | Chunk UUID | Vector rank / distance | BM25 rank / score | RRF rank / score | Rerank score |
|---:|---|---|---|---|---|---:|
| 1 | ml_supervised_learning_basics | `66277f9c-97b1-4aa9-885f-1a7cde13ffbe` | 2 / 0.978721738 | 1 / 11.782393076 | 1 / 0.032522475 | 5.000 |
| 2 | ml_classification_regression | `a991caeb-71fd-45b3-8fb8-aa3b541b8f91` | 1 / 0.843102694 | 3 / 9.480320325 | 2 / 0.032266458 | 3.950 |
| 3 | ml_supervised_learning_basics | `3ccba452-0e10-40ef-ade4-06a09c80b66c` | 3 / 1.013628840 | 2 / 11.572153672 | 3 / 0.032002048 | 3.900 |
| 4 | ml_bias_variance_generalization | `c79ae468-500a-4b28-a0c9-7fc0a499e8c7` | 7 / 1.292668819 | 5 / 6.402738419 | 4 / 0.030309989 | 2.850 |
| 5 | ml_bias_variance_generalization | `7e65c5f9-f3f4-472e-9ed7-d90595144002` | 8 / 1.308321357 | 6 / 4.987128914 | 5 / 0.029857398 | 2.800 |

### Exact heuristic contributions for fused candidates

| Fused rank | Document/chunk | UUID | Matched query tokens (repetitions counted) | Overlap + rank bonus = score |
|---:|---|---|---|---|
| 1 | ml_supervised_learning_basics/1 | `66277f9c-97b1-4aa9-885f-1a7cde13ffbe` | whether, price, supervised, learning | 4.00 + 1.00 = 5.00 |
| 2 | ml_classification_regression/0 | `a991caeb-71fd-45b3-8fb8-aa3b541b8f91` | price, supervised, learning | 3.00 + 0.95 = 3.95 |
| 3 | ml_supervised_learning_basics/0 | `3ccba452-0e10-40ef-ade4-06a09c80b66c` | whether, supervised, learning | 3.00 + 0.90 = 3.90 |
| 4 | ml_bias_variance_generalization/0 | `c79ae468-500a-4b28-a0c9-7fc0a499e8c7` | learning, explain | 2.00 + 0.85 = 2.85 |
| 5 | ml_bias_variance_generalization/1 | `7e65c5f9-f3f4-472e-9ed7-d90595144002` | learning, explain | 2.00 + 0.80 = 2.80 |
| 6 | ml_supervised_learning_basics/2 | `8e3c8941-518e-401e-961b-091b2c14a7cc` | price | 1.00 + 0.75 = 1.75 |
| 7 | ml/0 | `e3380555-fb30-454c-9a43-f8e3d66c05b9` | use, learning | 2.00 + 0.70 = 2.70 |
| 8 | ml_model_evaluation/0 | `6d045457-927e-4d91-a801-80fb6b49a451` | learning | 1.00 + 0.65 = 1.65 |
| 9 | ml_model_evaluation/1 | `bd664c0a-5bcb-457d-b326-bddcb215638f` | learning | 1.00 + 0.60 = 1.60 |
| 10 | ml_gradient_descent/0 | `4a373a64-f445-4926-964c-e32d4bef44e2` | learning | 1.00 + 0.55 = 1.55 |
| 11 | os_processes_threads_scheduling/2 | `5c0117ef-6ce2-4d21-b39b-adc2586cdaa6` | distinction | 1.00 + 0.50 = 1.50 |
| 12 | ml_overfitting_underfitting/0 | `d7755e05-d3c6-4865-9453-7d9464895375` |  | 0.00 + 0.45 = 0.45 |
| 13 | os_process_vs_thread/0 | `dbd54f08-345e-4f7f-aa82-2ab6bde2c3c3` | same | 1.00 + 0.40 = 1.40 |
| 14 | ml_bias_variance_generalization/2 | `238ddbf4-a7b9-4647-b485-79a96e6a48d5` |  | 0.00 + 0.35 = 0.35 |
| 15 | db_transactions_concurrency/2 | `b2b2b736-dbec-45ae-b811-77d5a03d785e` | same | 1.00 + 0.30 = 1.30 |

## retrieval_012

A predictor looks excellent on examples it practiced on but performs badly on unfamiliar examples. What learning problem does this suggest?

### Canonical evidence

**ml_overfitting_underfitting / chunk 0 / `d7755e05-d3c6-4865-9453-7d9464895375`**

Underfitting occurs when a model is too simple to capture patterns in the training data. Underfit models typically have high bias and poor performance on both training and test data. Overfitting occurs when a model learns noise and specific details of the training data instead of general patterns. Overfit models often perform well on training data but poorly on unseen data. Model complexity influences the balance between underfitting and overfitting.


### Alternatives from annotation notes

Semantic paraphrase of overfitting; canonical evidence directly states the training/unseen-performance pattern. Full equivalent evidence: 1a8573db-c271-4cd4-9bc8-097466513548 (ml_overfitting_underfitting, chunk 1); 66277f9c-97b1-4aa9-885f-1a7cde13ffbe (ml_supervised_learning_basics, chunk 1); 8e3c8941-518e-401e-961b-091b2c14a7cc (ml_supervised_learning_basics, chunk 2). Partial supporting evidence: c79ae468-500a-4b28-a0c9-7fc0a499e8c7 (ml_bias_variance_generalization, chunk 0); 7e65c5f9-f3f4-472e-9ed7-d90595144002 (ml_bias_variance_generalization, chunk 1); 238ddbf4-a7b9-4647-b485-79a96e6a48d5 (ml_bias_variance_generalization, chunk 2) discuss related explanations or warning signs rather than the same direct formulation.

**ml_overfitting_underfitting / chunk 1 / `1a8573db-c271-4cd4-9bc8-097466513548`**

Underfitting occurs when a model is too simple to capture patterns in the training data. Underfit models typically have high bias and poor performance on both training and test data. Overfitting occurs when a model learns noise and specific details of the training data instead of general patterns. Overfit models often perform well on training data but poorly on unseen data. Model complexity influences the balance between underfitting and overfitting. Techniques such as regularization, cross-validation, and collecting more data can help reduce overfitting. The bias-variance tradeoff explains the relationship between model complexity and generalization performance.

**ml_supervised_learning_basics / chunk 1 / `66277f9c-97b1-4aa9-885f-1a7cde13ffbe`**

Supervised learning is a machine learning paradigm in which a model learns from labeled examples. Each training example contains input features and a target output. The goal is to learn a mapping from inputs to outputs so that the model can generalize to unseen data. Supervised learning tasks are often divided into classification and regression. Classification predicts discrete categories, such as whether an email is spam or not spam. Regression predicts continuous values, such as the price of a house. During training, the model minimizes a loss function that measures the difference between predictions and true labels. Training error refers to performance on the training set, while test error refers to performance on new unseen data. A model that performs very well on training data but poorly on test data is said to be overfitting. A model that performs poorly even on training data may be underfitting.

**ml_supervised_learning_basics / chunk 2 / `8e3c8941-518e-401e-961b-091b2c14a7cc`**

Regression predicts continuous values, such as the price of a house. During training, the model minimizes a loss function that measures the difference between predictions and true labels. Training error refers to performance on the training set, while test error refers to performance on new unseen data. A model that performs very well on training data but poorly on test data is said to be overfitting. A model that performs poorly even on training data may be underfitting. Feature selection, regularization, and cross-validation are common techniques used to improve generalization.

**ml_bias_variance_generalization / chunk 0 / `c79ae468-500a-4b28-a0c9-7fc0a499e8c7`**

The bias-variance tradeoff helps explain prediction error in machine learning models. Bias refers to error caused by overly simplistic assumptions in the learning algorithm. High-bias models are usually too simple and may underfit the training data. Variance refers to error caused by excessive sensitivity to the training data. High-variance models may fit noise in the training set and therefore overfit. Good generalization requires balancing these two sources of error.

**ml_bias_variance_generalization / chunk 1 / `7e65c5f9-f3f4-472e-9ed7-d90595144002`**

The bias-variance tradeoff helps explain prediction error in machine learning models. Bias refers to error caused by overly simplistic assumptions in the learning algorithm. High-bias models are usually too simple and may underfit the training data. Variance refers to error caused by excessive sensitivity to the training data. High-variance models may fit noise in the training set and therefore overfit. Good generalization requires balancing these two sources of error. Increasing model complexity can reduce bias but may increase variance. Regularization can reduce variance by discouraging overly complex models. Cross-validation is used to estimate how well a model is likely to perform on unseen data. In k-fold cross-validation, the dataset is divided into k subsets, and the model is trained multiple times, each time leaving out one subset for validation. A gap between training accuracy and validation accuracy is often a sign of overfitting.

**ml_bias_variance_generalization / chunk 2 / `238ddbf4-a7b9-4647-b485-79a96e6a48d5`**

Increasing model complexity can reduce bias but may increase variance. Regularization can reduce variance by discouraging overly complex models. Cross-validation is used to estimate how well a model is likely to perform on unseen data. In k-fold cross-validation, the dataset is divided into k subsets, and the model is trained multiple times, each time leaving out one subset for validation. A gap between training accuracy and validation accuracy is often a sign of overfitting. Selecting a model is not only about maximizing training performance but about achieving robust performance on unseen examples.


### Ranking and score tables

Rank agreement with saved results: {'vector': True, 'bm25': True, 'hybrid': True, 'hybrid_reranked': True}

Reranker non-stopword question tokens: predictor, looks, excellent, examples, practiced, but, performs, badly, unfamiliar, examples, learning, problem, suggest

#### vector

| Rank | Document | Chunk UUID | Vector rank / distance | BM25 rank / score | RRF rank / score | Rerank score |
|---:|---|---|---|---|---|---:|
| 1 | ml_supervised_learning_basics | `8e3c8941-518e-401e-961b-091b2c14a7cc` | 1 / 1.036062002 | 6 / 5.539657175 | 1 / 0.031544958 | - |
| 2 | ml_bias_variance_generalization | `238ddbf4-a7b9-4647-b485-79a96e6a48d5` | 2 / 1.089647889 | 7 / 4.636823962 | 4 / 0.031054405 | - |
| 3 | ml_overfitting_underfitting | `d7755e05-d3c6-4865-9453-7d9464895375` | 3 / 1.092285633 | - | 9 / 0.015873016 | - |
| 4 | ml_overfitting_underfitting | `1a8573db-c271-4cd4-9bc8-097466513548` | 4 / 1.105240583 | - | 10 / 0.015625000 | - |
| 5 | ml_model_evaluation | `6d045457-927e-4d91-a801-80fb6b49a451` | 5 / 1.121196270 | 2 / 9.549679665 | 3 / 0.031513648 | - |

#### bm25

| Rank | Document | Chunk UUID | Vector rank / distance | BM25 rank / score | RRF rank / score | Rerank score |
|---:|---|---|---|---|---|---:|
| 1 | ml_supervised_learning_basics | `66277f9c-97b1-4aa9-885f-1a7cde13ffbe` | 6 / 1.125849009 | 1 / 9.635788836 | 2 / 0.031544958 | - |
| 2 | ml_model_evaluation | `6d045457-927e-4d91-a801-80fb6b49a451` | 5 / 1.121196270 | 2 / 9.549679665 | 3 / 0.031513648 | - |
| 3 | ml_model_evaluation | `bd664c0a-5bcb-457d-b326-bddcb215638f` | 8 / 1.172123790 | 3 / 7.913322239 | 5 / 0.030578898 | - |
| 4 | ml_supervised_learning_basics | `3ccba452-0e10-40ef-ade4-06a09c80b66c` | 10 / 1.256119013 | 4 / 6.081286976 | 6 / 0.029910714 | - |
| 5 | ml_classification_regression | `a991caeb-71fd-45b3-8fb8-aa3b541b8f91` | - | 5 / 6.071573779 | 11 / 0.015384615 | - |

#### hybrid

| Rank | Document | Chunk UUID | Vector rank / distance | BM25 rank / score | RRF rank / score | Rerank score |
|---:|---|---|---|---|---|---:|
| 1 | ml_supervised_learning_basics | `8e3c8941-518e-401e-961b-091b2c14a7cc` | 1 / 1.036062002 | 6 / 5.539657175 | 1 / 0.031544958 | - |
| 2 | ml_supervised_learning_basics | `66277f9c-97b1-4aa9-885f-1a7cde13ffbe` | 6 / 1.125849009 | 1 / 9.635788836 | 2 / 0.031544958 | - |
| 3 | ml_model_evaluation | `6d045457-927e-4d91-a801-80fb6b49a451` | 5 / 1.121196270 | 2 / 9.549679665 | 3 / 0.031513648 | - |
| 4 | ml_bias_variance_generalization | `238ddbf4-a7b9-4647-b485-79a96e6a48d5` | 2 / 1.089647889 | 7 / 4.636823962 | 4 / 0.031054405 | - |
| 5 | ml_model_evaluation | `bd664c0a-5bcb-457d-b326-bddcb215638f` | 8 / 1.172123790 | 3 / 7.913322239 | 5 / 0.030578898 | - |

#### hybrid_reranked

| Rank | Document | Chunk UUID | Vector rank / distance | BM25 rank / score | RRF rank / score | Rerank score |
|---:|---|---|---|---|---|---:|
| 1 | ml_supervised_learning_basics | `66277f9c-97b1-4aa9-885f-1a7cde13ffbe` | 6 / 1.125849009 | 1 / 9.635788836 | 2 / 0.031544958 | 5.950 |
| 2 | ml_model_evaluation | `6d045457-927e-4d91-a801-80fb6b49a451` | 5 / 1.121196270 | 2 / 9.549679665 | 3 / 0.031513648 | 5.900 |
| 3 | ml_model_evaluation | `bd664c0a-5bcb-457d-b326-bddcb215638f` | 8 / 1.172123790 | 3 / 7.913322239 | 5 / 0.030578898 | 5.800 |
| 4 | ml_bias_variance_generalization | `238ddbf4-a7b9-4647-b485-79a96e6a48d5` | 2 / 1.089647889 | 7 / 4.636823962 | 4 / 0.031054405 | 3.850 |
| 5 | ml_supervised_learning_basics | `3ccba452-0e10-40ef-ade4-06a09c80b66c` | 10 / 1.256119013 | 4 / 6.081286976 | 6 / 0.029910714 | 3.750 |

### Exact heuristic contributions for fused candidates

| Fused rank | Document/chunk | UUID | Matched query tokens (repetitions counted) | Overlap + rank bonus = score |
|---:|---|---|---|---|
| 1 | ml_supervised_learning_basics/2 | `8e3c8941-518e-401e-961b-091b2c14a7cc` | but, performs | 2.00 + 1.00 = 3.00 |
| 2 | ml_supervised_learning_basics/1 | `66277f9c-97b1-4aa9-885f-1a7cde13ffbe` | examples, but, performs, examples, learning | 5.00 + 0.95 = 5.95 |
| 3 | ml_model_evaluation/0 | `6d045457-927e-4d91-a801-80fb6b49a451` | examples, but, performs, examples, learning | 5.00 + 0.90 = 5.90 |
| 4 | ml_bias_variance_generalization/2 | `238ddbf4-a7b9-4647-b485-79a96e6a48d5` | examples, but, examples | 3.00 + 0.85 = 3.85 |
| 5 | ml_model_evaluation/1 | `bd664c0a-5bcb-457d-b326-bddcb215638f` | examples, but, performs, examples, learning | 5.00 + 0.80 = 5.80 |
| 6 | ml_supervised_learning_basics/0 | `3ccba452-0e10-40ef-ade4-06a09c80b66c` | examples, examples, learning | 3.00 + 0.75 = 3.75 |
| 7 | ml_bias_variance_generalization/1 | `7e65c5f9-f3f4-472e-9ed7-d90595144002` | but, learning | 2.00 + 0.70 = 2.70 |
| 8 | ml_bias_variance_generalization/0 | `c79ae468-500a-4b28-a0c9-7fc0a499e8c7` | learning | 1.00 + 0.65 = 1.65 |
| 9 | ml_overfitting_underfitting/0 | `d7755e05-d3c6-4865-9453-7d9464895375` | but | 1.00 + 0.60 = 1.60 |
| 10 | ml_overfitting_underfitting/1 | `1a8573db-c271-4cd4-9bc8-097466513548` | but | 1.00 + 0.55 = 1.55 |
| 11 | ml_classification_regression/0 | `a991caeb-71fd-45b3-8fb8-aa3b541b8f91` | examples, examples, learning | 3.00 + 0.50 = 3.50 |
| 12 | ml_gradient_descent/0 | `4a373a64-f445-4926-964c-e32d4bef44e2` | learning | 1.00 + 0.45 = 1.45 |

## retrieval_015

What does atomicity guarantee for a database transaction, and what does precision measure for a classifier?

### Canonical evidence

**db_transactions_concurrency / chunk 0 / `0dd5a5bf-5dab-4d48-b5f3-566ff4b80281`**

A transaction is a logical unit of work that must either complete entirely or have no effect at all. The ACID properties describe the reliability of transactions. Atomicity means all operations of a transaction happen or none happen. Consistency means the database moves from one valid state to another valid state. Isolation means concurrent transactions should not interfere in a way that produces incorrect results.

**ml_model_evaluation / chunk 0 / `6d045457-927e-4d91-a801-80fb6b49a451`**

Model evaluation measures how well a machine learning model performs on unseen data. A model should not only fit the training data but also generalize to new examples. A confusion matrix summarizes classification results using true positives, true negatives, false positives, and false negatives. Accuracy measures the proportion of correct predictions. Accuracy can be misleading on imbalanced datasets. Precision measures how many predicted positive instances are actually positive.


### Alternatives from annotation notes

Complementary canonical evidence covers two separate topics. Component substitutes: ece01229-7d42-455a-a3e2-cf789c5dae2c (db_transactions_concurrency, chunk 1) can replace the atomicity chunk; bd664c0a-5bcb-457d-b326-bddcb215638f (ml_model_evaluation, chunk 1) can replace the precision chunk. Neither substitute covers both parts.

**db_transactions_concurrency / chunk 1 / `ece01229-7d42-455a-a3e2-cf789c5dae2c`**

A transaction is a logical unit of work that must either complete entirely or have no effect at all. The ACID properties describe the reliability of transactions. Atomicity means all operations of a transaction happen or none happen. Consistency means the database moves from one valid state to another valid state. Isolation means concurrent transactions should not interfere in a way that produces incorrect results. Durability means that once a transaction is committed, its effects persist even after a crash. Concurrency control is needed because many users may access the same data at the same time. Problems that can appear without proper control include lost updates, dirty reads, and non-repeatable reads. A lost update occurs when one transaction overwrites the result of another. A dirty read happens when a transaction reads data written by another transaction that has not yet committed.

**ml_model_evaluation / chunk 1 / `bd664c0a-5bcb-457d-b326-bddcb215638f`**

Model evaluation measures how well a machine learning model performs on unseen data. A model should not only fit the training data but also generalize to new examples. A confusion matrix summarizes classification results using true positives, true negatives, false positives, and false negatives. Accuracy measures the proportion of correct predictions. Accuracy can be misleading on imbalanced datasets. Precision measures how many predicted positive instances are actually positive. Recall measures how many actual positive instances are correctly identified. The F1 score combines precision and recall into a single metric and is useful when both are important. Cross-validation is often used to obtain a more reliable estimate of model performance.


### Ranking and score tables

Rank agreement with saved results: {'vector': True, 'bm25': True, 'hybrid': True, 'hybrid_reranked': True}

Reranker non-stopword question tokens: atomicity, guarantee, database, transaction, precision, measure, classifier

#### vector

| Rank | Document | Chunk UUID | Vector rank / distance | BM25 rank / score | RRF rank / score | Rerank score |
|---:|---|---|---|---|---|---:|
| 1 | db_transactions_concurrency | `0dd5a5bf-5dab-4d48-b5f3-566ff4b80281` | 1 / 0.937348187 | 1 / 11.467504044 | 1 / 0.032786885 | - |
| 2 | db_transactions_concurrency | `ece01229-7d42-455a-a3e2-cf789c5dae2c` | 2 / 0.949703693 | 2 / 10.148160559 | 2 / 0.032258065 | - |
| 3 | ml_model_evaluation | `6d045457-927e-4d91-a801-80fb6b49a451` | 3 / 1.122532368 | 5 / 3.562697730 | 4 / 0.031257631 | - |
| 4 | db_transactions_concurrency | `b2b2b736-dbec-45ae-b811-77d5a03d785e` | 4 / 1.138150811 | 3 / 5.284815576 | 3 / 0.031498016 | - |
| 5 | ml_model_evaluation | `bd664c0a-5bcb-457d-b326-bddcb215638f` | 5 / 1.174918890 | 4 / 4.172771798 | 5 / 0.031009615 | - |

#### bm25

| Rank | Document | Chunk UUID | Vector rank / distance | BM25 rank / score | RRF rank / score | Rerank score |
|---:|---|---|---|---|---|---:|
| 1 | db_transactions_concurrency | `0dd5a5bf-5dab-4d48-b5f3-566ff4b80281` | 1 / 0.937348187 | 1 / 11.467504044 | 1 / 0.032786885 | - |
| 2 | db_transactions_concurrency | `ece01229-7d42-455a-a3e2-cf789c5dae2c` | 2 / 0.949703693 | 2 / 10.148160559 | 2 / 0.032258065 | - |
| 3 | db_transactions_concurrency | `b2b2b736-dbec-45ae-b811-77d5a03d785e` | 4 / 1.138150811 | 3 / 5.284815576 | 3 / 0.031498016 | - |
| 4 | ml_model_evaluation | `bd664c0a-5bcb-457d-b326-bddcb215638f` | 5 / 1.174918890 | 4 / 4.172771798 | 5 / 0.031009615 | - |
| 5 | ml_model_evaluation | `6d045457-927e-4d91-a801-80fb6b49a451` | 3 / 1.122532368 | 5 / 3.562697730 | 4 / 0.031257631 | - |

#### hybrid

| Rank | Document | Chunk UUID | Vector rank / distance | BM25 rank / score | RRF rank / score | Rerank score |
|---:|---|---|---|---|---|---:|
| 1 | db_transactions_concurrency | `0dd5a5bf-5dab-4d48-b5f3-566ff4b80281` | 1 / 0.937348187 | 1 / 11.467504044 | 1 / 0.032786885 | - |
| 2 | db_transactions_concurrency | `ece01229-7d42-455a-a3e2-cf789c5dae2c` | 2 / 0.949703693 | 2 / 10.148160559 | 2 / 0.032258065 | - |
| 3 | db_transactions_concurrency | `b2b2b736-dbec-45ae-b811-77d5a03d785e` | 4 / 1.138150811 | 3 / 5.284815576 | 3 / 0.031498016 | - |
| 4 | ml_model_evaluation | `6d045457-927e-4d91-a801-80fb6b49a451` | 3 / 1.122532368 | 5 / 3.562697730 | 4 / 0.031257631 | - |
| 5 | ml_model_evaluation | `bd664c0a-5bcb-457d-b326-bddcb215638f` | 5 / 1.174918890 | 4 / 4.172771798 | 5 / 0.031009615 | - |

#### hybrid_reranked

| Rank | Document | Chunk UUID | Vector rank / distance | BM25 rank / score | RRF rank / score | Rerank score |
|---:|---|---|---|---|---|---:|
| 1 | db_transactions_concurrency | `0dd5a5bf-5dab-4d48-b5f3-566ff4b80281` | 1 / 0.937348187 | 1 / 11.467504044 | 1 / 0.032786885 | 4.000 |
| 2 | db_transactions_concurrency | `ece01229-7d42-455a-a3e2-cf789c5dae2c` | 2 / 0.949703693 | 2 / 10.148160559 | 2 / 0.032258065 | 3.950 |
| 3 | db_transactions_concurrency | `b2b2b736-dbec-45ae-b811-77d5a03d785e` | 4 / 1.138150811 | 3 / 5.284815576 | 3 / 0.031498016 | 1.900 |
| 4 | ml_model_evaluation | `6d045457-927e-4d91-a801-80fb6b49a451` | 3 / 1.122532368 | 5 / 3.562697730 | 4 / 0.031257631 | 1.850 |
| 5 | ml_model_evaluation | `bd664c0a-5bcb-457d-b326-bddcb215638f` | 5 / 1.174918890 | 4 / 4.172771798 | 5 / 0.031009615 | 1.800 |

### Exact heuristic contributions for fused candidates

| Fused rank | Document/chunk | UUID | Matched query tokens (repetitions counted) | Overlap + rank bonus = score |
|---:|---|---|---|---|
| 1 | db_transactions_concurrency/0 | `0dd5a5bf-5dab-4d48-b5f3-566ff4b80281` | atomicity, database, transaction | 3.00 + 1.00 = 4.00 |
| 2 | db_transactions_concurrency/1 | `ece01229-7d42-455a-a3e2-cf789c5dae2c` | atomicity, database, transaction | 3.00 + 0.95 = 3.95 |
| 3 | db_transactions_concurrency/2 | `b2b2b736-dbec-45ae-b811-77d5a03d785e` | transaction | 1.00 + 0.90 = 1.90 |
| 4 | ml_model_evaluation/0 | `6d045457-927e-4d91-a801-80fb6b49a451` | precision | 1.00 + 0.85 = 1.85 |
| 5 | ml_model_evaluation/1 | `bd664c0a-5bcb-457d-b326-bddcb215638f` | precision | 1.00 + 0.80 = 1.80 |
| 6 | db_normalization_intro/1 | `f47f5e9c-59a3-4859-8580-c16ffb34ed60` | database | 1.00 + 0.75 = 1.75 |
| 7 | db_normalization_intro/0 | `a1cbb9b1-26d3-4a25-a6db-73d26dc8eb68` | database | 1.00 + 0.70 = 1.70 |
| 8 | ml_classification_regression/0 | `a991caeb-71fd-45b3-8fb8-aa3b541b8f91` |  | 0.00 + 0.65 = 0.65 |
| 9 | db_normalization_intro/2 | `73c987b6-90bc-41e1-bbb7-12bc713de952` |  | 0.00 + 0.60 = 0.60 |
| 10 | ml_supervised_learning_basics/2 | `8e3c8941-518e-401e-961b-091b2c14a7cc` |  | 0.00 + 0.55 = 0.55 |

## retrieval_016

Which execution-state items remain private to each thread even though threads share their process's memory and resources?

### Canonical evidence

**os_process_vs_thread / chunk 0 / `dbd54f08-345e-4f7f-aa82-2ab6bde2c3c3`**

A process is an independent program in execution. Each process has its own memory space, resources, and execution state. A thread is the smallest unit of execution within a process. Threads that belong to the same process share the same memory space and resources, but each thread has its own stack and program counter. Processes are more isolated than threads.


### Alternatives from annotation notes

Canonical evidence explicitly names the private stack and program counter alongside shared memory/resources. Full equivalent evidence: a4d8fe4d-300d-49b7-b7a9-c573f06af200 (os_process_vs_thread, chunk 1) repeats this passage.

**os_process_vs_thread / chunk 1 / `a4d8fe4d-300d-49b7-b7a9-c573f06af200`**

A process is an independent program in execution. Each process has its own memory space, resources, and execution state. A thread is the smallest unit of execution within a process. Threads that belong to the same process share the same memory space and resources, but each thread has its own stack and program counter. Processes are more isolated than threads. Because each process has its own memory space, communication between processes usually requires inter-process communication mechanisms such as pipes, sockets, or shared memory. Threads communicate more easily because they share memory. This makes threads more efficient for tasks that need frequent communication, but it also introduces risks such as race conditions and synchronization problems.


### Ranking and score tables

Rank agreement with saved results: {'vector': True, 'bm25': True, 'hybrid': True, 'hybrid_reranked': True}

Reranker non-stopword question tokens: which, execution, state, items, remain, private, each, thread, even, though, threads, share, their, process, s, memory, resources

#### vector

| Rank | Document | Chunk UUID | Vector rank / distance | BM25 rank / score | RRF rank / score | Rerank score |
|---:|---|---|---|---|---|---:|
| 1 | os_process_vs_thread | `a4d8fe4d-300d-49b7-b7a9-c573f06af200` | 1 / 0.680017173 | 3 / 29.388223034 | 2 / 0.032266458 | - |
| 2 | os_process_vs_thread | `dbd54f08-345e-4f7f-aa82-2ab6bde2c3c3` | 2 / 0.683400631 | 1 / 31.396096918 | 1 / 0.032522475 | - |
| 3 | os_processes_threads_scheduling | `0c277ad4-37e2-4378-ae31-64e52a11d86a` | 3 / 0.710029185 | 2 / 29.705083865 | 3 / 0.032002048 | - |
| 4 | os_processes_threads_scheduling | `035326e9-1a04-4aed-9dc8-221befcf1945` | 4 / 0.775550246 | 4 / 26.981551670 | 4 / 0.031250000 | - |
| 5 | os_process_vs_thread | `28a7c7fa-ee37-43be-a91c-7243ed15b0ac` | 5 / 0.934499979 | 5 / 15.927556626 | 5 / 0.030769231 | - |

#### bm25

| Rank | Document | Chunk UUID | Vector rank / distance | BM25 rank / score | RRF rank / score | Rerank score |
|---:|---|---|---|---|---|---:|
| 1 | os_process_vs_thread | `dbd54f08-345e-4f7f-aa82-2ab6bde2c3c3` | 2 / 0.683400631 | 1 / 31.396096918 | 1 / 0.032522475 | - |
| 2 | os_processes_threads_scheduling | `0c277ad4-37e2-4378-ae31-64e52a11d86a` | 3 / 0.710029185 | 2 / 29.705083865 | 3 / 0.032002048 | - |
| 3 | os_process_vs_thread | `a4d8fe4d-300d-49b7-b7a9-c573f06af200` | 1 / 0.680017173 | 3 / 29.388223034 | 2 / 0.032266458 | - |
| 4 | os_processes_threads_scheduling | `035326e9-1a04-4aed-9dc8-221befcf1945` | 4 / 0.775550246 | 4 / 26.981551670 | 4 / 0.031250000 | - |
| 5 | os_process_vs_thread | `28a7c7fa-ee37-43be-a91c-7243ed15b0ac` | 5 / 0.934499979 | 5 / 15.927556626 | 5 / 0.030769231 | - |

#### hybrid

| Rank | Document | Chunk UUID | Vector rank / distance | BM25 rank / score | RRF rank / score | Rerank score |
|---:|---|---|---|---|---|---:|
| 1 | os_process_vs_thread | `dbd54f08-345e-4f7f-aa82-2ab6bde2c3c3` | 2 / 0.683400631 | 1 / 31.396096918 | 1 / 0.032522475 | - |
| 2 | os_process_vs_thread | `a4d8fe4d-300d-49b7-b7a9-c573f06af200` | 1 / 0.680017173 | 3 / 29.388223034 | 2 / 0.032266458 | - |
| 3 | os_processes_threads_scheduling | `0c277ad4-37e2-4378-ae31-64e52a11d86a` | 3 / 0.710029185 | 2 / 29.705083865 | 3 / 0.032002048 | - |
| 4 | os_processes_threads_scheduling | `035326e9-1a04-4aed-9dc8-221befcf1945` | 4 / 0.775550246 | 4 / 26.981551670 | 4 / 0.031250000 | - |
| 5 | os_process_vs_thread | `28a7c7fa-ee37-43be-a91c-7243ed15b0ac` | 5 / 0.934499979 | 5 / 15.927556626 | 5 / 0.030769231 | - |

#### hybrid_reranked

| Rank | Document | Chunk UUID | Vector rank / distance | BM25 rank / score | RRF rank / score | Rerank score |
|---:|---|---|---|---|---|---:|
| 1 | os_processes_threads_scheduling | `035326e9-1a04-4aed-9dc8-221befcf1945` | 4 / 0.775550246 | 4 / 26.981551670 | 4 / 0.031250000 | 10.850 |
| 2 | os_process_vs_thread | `dbd54f08-345e-4f7f-aa82-2ab6bde2c3c3` | 2 / 0.683400631 | 1 / 31.396096918 | 1 / 0.032522475 | 10.000 |
| 3 | os_process_vs_thread | `a4d8fe4d-300d-49b7-b7a9-c573f06af200` | 1 / 0.680017173 | 3 / 29.388223034 | 2 / 0.032266458 | 9.950 |
| 4 | os_processes_threads_scheduling | `0c277ad4-37e2-4378-ae31-64e52a11d86a` | 3 / 0.710029185 | 2 / 29.705083865 | 3 / 0.032002048 | 9.900 |
| 5 | os_process_vs_thread | `28a7c7fa-ee37-43be-a91c-7243ed15b0ac` | 5 / 0.934499979 | 5 / 15.927556626 | 5 / 0.030769231 | 6.800 |

### Exact heuristic contributions for fused candidates

| Fused rank | Document/chunk | UUID | Matched query tokens (repetitions counted) | Overlap + rank bonus = score |
|---:|---|---|---|---|
| 1 | os_process_vs_thread/0 | `dbd54f08-345e-4f7f-aa82-2ab6bde2c3c3` | execution, state, each, thread, threads, share, process, memory, resources | 9.00 + 1.00 = 10.00 |
| 2 | os_process_vs_thread/1 | `a4d8fe4d-300d-49b7-b7a9-c573f06af200` | execution, state, each, thread, threads, share, process, memory, resources | 9.00 + 0.95 = 9.95 |
| 3 | os_processes_threads_scheduling/0 | `0c277ad4-37e2-4378-ae31-64e52a11d86a` | which, execution, state, thread, threads, share, process, memory, resources | 9.00 + 0.90 = 9.90 |
| 4 | os_processes_threads_scheduling/1 | `035326e9-1a04-4aed-9dc8-221befcf1945` | which, execution, state, each, thread, threads, share, process, memory, resources | 10.00 + 0.85 = 10.85 |
| 5 | os_process_vs_thread/2 | `28a7c7fa-ee37-43be-a91c-7243ed15b0ac` | each, thread, threads, share, process, memory | 6.00 + 0.80 = 6.80 |
| 6 | os_process_vs_thread/3 | `fddc7e74-63c8-4d3b-b343-a3aa1d8d7987` | execution, thread, threads, process | 4.00 + 0.75 = 4.75 |
| 7 | os_processes_threads_scheduling/2 | `5c0117ef-6ce2-4d21-b39b-adc2586cdaa6` | which, each, thread, process | 4.00 + 0.70 = 4.70 |
| 8 | db_transactions_concurrency/1 | `ece01229-7d42-455a-a3e2-cf789c5dae2c` | state, even | 2.00 + 0.65 = 2.65 |
| 9 | db_transactions_concurrency/2 | `b2b2b736-dbec-45ae-b811-77d5a03d785e` | even | 1.00 + 0.60 = 1.60 |
| 10 | ml_supervised_learning_basics/1 | `66277f9c-97b1-4aa9-885f-1a7cde13ffbe` | which, each, even | 3.00 + 0.55 = 3.55 |
| 11 | db_transactions_concurrency/0 | `0dd5a5bf-5dab-4d48-b5f3-566ff4b80281` | state | 1.00 + 0.50 = 1.50 |
| 12 | db_normalization_intro/1 | `f47f5e9c-59a3-4859-8580-c16ffb34ed60` | which, each, process | 3.00 + 0.45 = 3.45 |


## Factual diagnosis

- 002: ME0 and ME1 tie at RRF 0.032522475 because ranks (1,2) and (2,1) contribute the same sum. Stable fusion ordering keeps ME0 first. The reranker promotes ME1 because its extra F1 passage contains `when` and `metric`: six matched tokens + 0.95 = 6.95 versus four + 1.00 = 5.00. Both contain the accuracy/imbalance evidence.
- 003: PT2 and PT1 similarly tie in RRF. PS1 gains the token `sharing` from `time-sharing systems`, raising its reranker score to 5.85 above PT2 5.00 and PT1 4.95. Its basic comparison is supporting evidence; the incidental extra match comes from scheduling.
- 008: NI1 gains `which` from the unrelated anomaly sentence `which can cause update anomalies`. Query token `dependency` is counted twice for both chunks. NI1 obtains nine matches + 0.95 = 9.95, versus NI2 eight + 1.00 = 9.00. The required definitions are equivalent.
- 009: TC2 vector rank 1/BM25 rank 5 yields 0.031778058. TC1 ranks 2/1 yield 0.032522475; TC0 ranks 3/2 yield 0.032002048. RRF does not consider TC2's stronger distance margin. TC1 matches `database`, `means`, `even`, scoring 9.228671 BM25; TC2 matches `means`, `even`, scoring 5.288697. Reranking adds a supervised-learning distractor matching `which`, `even`, `machine`, scoring 3.65; TC2 scores 2.90 and falls to rank 4. TC1 is full equivalent durability evidence; TC0 lacks durability.
- 010: TC2 matches `one`, `same`, `different`, `because`, totaling BM25 11.473730. NI1 matches `one`, `database`, `same`, `information`, `changed`, totaling 11.398852. NI0 totals 9.810408. Vector prefers NI0 (distance 1.122326) to TC2 (1.209409), consistent with the question's shared facts/changed-data wording, though the embedding's internal cause cannot be proved. NI0 and TC2 tie in RRF; stable ordering keeps NI0 first. Reranking prefers NI1's five keyword matches to TC2's four, despite NI1 lacking the non-repeatable-read answer.
- 011: SL1 matches `whether`, `price`, `supervised`, `learning`; CR0 lacks `whether`. BM25 ranks SL1 first/CR0 third. RRF ranks (2,1) give SL1 0.032522475 versus CR0 (1,3) 0.032266458. Reranking preserves SL1 via five versus 3.95 total score. SL1 is full equivalent evidence for the classification/regression comparison.
- 012: OU0 is vector rank 3 but absent from BM25 top 10. It obtains only 1/63=0.015873016, fused rank 9. SL2 and SL1 each obtain 0.031544958 from agreement; both explicitly answer overfitting. Generic model-evaluation passages also match the query words. The reranker counts repeated `examples` twice; SL1, ME0, ME1 each have five matches, scoring 5.95/5.90/5.80. OU0 matches only `but`, scoring 1.60. Canonical UUID coverage fails, but returned SL1/SL2 evidence supports the answer. Generic ME passages are genuine distractors.
- 015: TC2 matches only `transaction` but occurs at ranks vector 4/BM25 3. RRF 0.031498016 beats ME0 ranks 3/5, score 0.031257631. Duplicate TC0/TC1 occupy the first two positions. The precision component moves from vector rank 3 to fused rank 4. Reranking uses one match for each and preserves the 0.05 fused-rank advantage for TC2. Both canonical components remain within five.
- 016: BM25 favors focused PT0 (31.396097) over extended PT1 (29.388223), whereas vector distances 0.683401/0.680017 narrowly favor PT1. Fusion ranks (2,1) versus (1,3) put PT0 first. PS1 gains `which` and `each` in scheduling sentences and has ten matched tokens + 0.85 = 10.85. PT0 has nine + 1.00 = 10.00. PS1 lacks the private stack/program-counter fact. PT1 is a full equivalent alternative; PS1 is only related process/thread context for this question.

## Issue classification

| Query | Primary classifications | Evidence interpretation |
|---|---|---|
| 002 | Benchmark/canonical-label artifact; corpus/chunking overlap artifact; reranker issue | Equivalent answer evidence swaps order because incidental keywords count. |
| 003 | Benchmark/canonical-label artifact; corpus/chunking overlap artifact; reranker issue | Equivalent/basic comparison evidence dominates; `sharing` from scheduling changes order. |
| 008 | Benchmark/canonical-label artifact; corpus/chunking overlap artifact; reranker issue | Equivalent definitions swap order because unrelated `which` matches. |
| 009 | Fusion issue; reranker issue; benchmark/canonical-label artifact | Equivalent durability evidence comes first, but a passage without durability and an ML distractor also overtake the canonical chunk. |
| 010 | Retrieval algorithm issue; fusion issue; reranker issue | Normalization distractors overtake the non-repeatable-read answer; BM25 ranks the actual answer first. |
| 011 | Benchmark/canonical-label artifact | The leading alternative fully answers the comparison. |
| 012 | Benchmark/canonical-label artifact; fusion issue; reranker issue | Complete alternative evidence is retrieved, while generic evaluation distractors displace canonical evidence. |
| 015 | Fusion issue; corpus/chunking overlap artifact; reranker issue | Duplicate atomicity passages and a transaction-only distractor delay the precision component. |
| 016 | Reranker issue; benchmark/canonical-label artifact; corpus/chunking overlap artifact | Incidental scheduling words promote a chunk missing the private-state fact. |

No fixes are proposed in this analysis. No retrieval code, labels, metrics, or runner code was changed.
