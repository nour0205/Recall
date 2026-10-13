# Benchmark v3 draft: review sheet

Generated from `benchmark_v3_draft.json` by `python -m evaluation.benchmark_draft --render`; edit the JSON, not this file.

For each question, check: is it clear, is the reference answer right, are the required points the right ones, and for refuse cases, are the notes really silent on it?

| Category | Questions | Tests |
|---|---:|---|
| paraphrase | 10 | Asks about a fact without the notes' key words; needs semantic search. |
| exact_term | 8 | Hinges on a precise technical term; needs keyword search. |
| cross_note | 6 | Needs evidence from two different notes. |
| multi_part | 6 | Several requested parts from one note; tests completeness. |
| qualifier | 4 | Tempts the answer to drop a qualifier such as may, often or usually. |
| near_miss_refusal | 10 | The topic is in the notes but the requested detail is not. |
| out_of_scope | 4 | The topic is not in the notes at all. |

**Total:** 48 (34 answerable, 14 refusals)

## v3_001 · paraphrase · answer

**Q:** What can happen when the steps an optimizer takes are far too small?

**Reference:** If the learning rate (step size) is too small, gradient descent may converge slowly.
- `slow_convergence`: A learning rate that is too small may result in slow convergence.
  - ml_gradient_descent: "A learning rate that is too small may result in slow convergence."

*Notes:* Preserve may. The question never says learning rate or convergence.

## v3_002 · paraphrase · answer

**Q:** What do we call choosing, reshaping and inventing the inputs a model uses from raw data?

**Reference:** Feature engineering: selecting, transforming and creating useful features from raw data.
- `feature_engineering`: This is feature engineering: selecting, transforming and creating useful features from raw data.
  - ml_feature_engineering: "Feature engineering is the process of selecting, transforming, and creating useful features from raw data."

*Notes:* Naming feature engineering is the core point.

## v3_003 · paraphrase · answer

**Q:** Which transformation makes every input have an average of zero and a spread of one?

**Reference:** Standardization, which transforms values to have zero mean and unit variance.
- `standardization`: Standardization transforms values to zero mean and unit variance.
  - ml_feature_engineering: "Standardization transforms values so they have zero mean and unit variance."

*Notes:* Must not answer normalization, which rescales to a range.

## v3_004 · paraphrase · answer

**Q:** My report used numbers that another user had changed but then cancelled before saving. Which concurrency problem is this?

**Reference:** A dirty read: a transaction reads data written by another transaction that has not yet committed.
- `dirty_read`: This is a dirty read: reading data written by another transaction that has not yet committed.
  - db_transactions_concurrency: "A dirty read happens when a transaction reads data written by another transaction that has not yet committed."

*Notes:* The name alone is not enough; the uncommitted-data mechanism is required.

## v3_005 · paraphrase · answer

**Q:** Two people edit the same record at the same time and one person's change silently disappears. What is this called?

**Reference:** A lost update, where one transaction overwrites the result of another.
- `lost_update`: This is a lost update: one transaction overwrites the result of another.
  - db_transactions_concurrency: "A lost update occurs when one transaction overwrites the result of another."

*Notes:* Name and mechanism both required.

## v3_006 · paraphrase · answer

**Q:** Why is switching between two separate running programs slower than switching between two workers inside the same program?

**Reference:** Switching between processes is generally more expensive than switching between threads, because more state must be saved and restored and processes require more operating-system overhead.
- `more_expensive`: Switching between processes is generally more expensive than switching between threads.
  - os_processes_threads_scheduling: "Context switching between processes is generally more expensive than switching between threads because more state must be saved and restored."
  - os_process_vs_thread: "Creating and switching between processes is generally more expensive than creating and switching between threads because processes require more operating system overhead."
- `reason`: Because more state must be saved and restored (more operating system overhead).
  - os_processes_threads_scheduling: "because more state must be saved and restored"
  - os_process_vs_thread: "because processes require more operating system overhead"

*Notes:* Either reason satisfies the reason point. Preserve generally.

## v3_007 · paraphrase · answer

**Q:** What do you call a model that is too simple and does badly even on the data it learned from?

**Reference:** Underfitting: the model is too simple to capture the patterns in the training data, so it performs poorly even there.
- `underfitting`: This is underfitting: the model is too simple to capture patterns in the training data.
  - ml_overfitting_underfitting: "Underfitting occurs when a model is too simple to capture patterns in the training data."
  - ml_supervised_learning_basics: "A model that performs poorly even on training data may be underfitting."

*Notes:* Naming underfitting with its meaning is required.

## v3_008 · paraphrase · answer

**Q:** What is it called when one large table is split into several smaller ones while keeping what the data means?

**Reference:** Decomposition, which splits a table into smaller relations while preserving data meaning.
- `decomposition`: Decomposition splits a table into smaller relations while preserving data meaning.
  - db_normalization_intro: "Decomposition is often used to split such a table into smaller relations while preserving data meaning."

*Notes:* The question avoids the words relation, decompose and normalization.

## v3_009 · paraphrase · answer

**Q:** What kind of learning uses examples that each come with the correct answer attached?

**Reference:** Supervised learning: the model learns from labeled examples, each with input features and a target output.
- `supervised`: Supervised learning, in which a model learns from labeled examples.
  - ml_supervised_learning_basics: "Supervised learning is a machine learning paradigm in which a model learns from labeled examples."

*Notes:* The question avoids the words supervised and labeled.

## v3_010 · paraphrase · answer

**Q:** Which way of sharing the processor gives every task a fixed slice of time in turn, and what does that improve?

**Reference:** Round robin: each process gets a fixed time quantum in turn, which improves responsiveness in time-sharing systems.
- `round_robin`: Round robin assigns each process a fixed time quantum and cycles through ready tasks.
  - os_processes_threads_scheduling: "Round robin assigns each process a fixed time quantum and cycles through ready tasks"
- `responsiveness`: It improves responsiveness in time-sharing systems.
  - os_processes_threads_scheduling: "which improves responsiveness in time-sharing systems"

*Notes:* Both parts required.

## v3_011 · exact_term · answer

**Q:** What does 1NF require?

**Reference:** The first normal form requires atomic attribute values and no repeating groups.
- `atomic_values`: Each attribute must contain atomic values.
  - db_normalization_intro: "The first normal form requires that each attribute contain atomic values and that there are no repeating groups."
- `no_repeating_groups`: There must be no repeating groups.
  - db_normalization_intro: "there are no repeating groups"

*Notes:* The notes write 'first normal form', never '1NF'. Mapping the abbreviation is acceptable; the content must come from the notes.

## v3_012 · exact_term · answer

**Q:** What does the D in ACID stand for, and what does it guarantee?

**Reference:** Durability: once a transaction is committed, its effects persist even after a crash.
- `durability`: D stands for durability.
  - db_transactions_concurrency: "Durability means that once a transaction is committed, its effects persist even after a crash."
- `persist_after_crash`: Once a transaction is committed, its effects persist even after a crash.
  - db_transactions_concurrency: "once a transaction is committed, its effects persist even after a crash"

*Notes:* Both the name and the guarantee are required.

## v3_013 · exact_term · answer

**Q:** Besides locking, which approach to handling concurrency do the notes mention?

**Reference:** Multiversion concurrency control.
- `mvcc`: Multiversion concurrency control.
  - db_transactions_concurrency: "Locking and multiversion concurrency control are two common approaches to handling concurrency."

*Notes:* The notes do not explain how it works; an answer that adds a mechanism is ungrounded.

## v3_014 · exact_term · answer

**Q:** Which inter-process communication mechanisms are listed, and why are they needed?

**Reference:** Pipes, sockets and shared memory. Because each process has its own memory space, communication between processes usually requires such mechanisms.
- `mechanisms`: Pipes, sockets and shared memory.
  - os_process_vs_thread: "inter-process communication mechanisms such as pipes, sockets, or shared memory"
- `own_memory`: Because each process has its own memory space, communication between processes usually requires them.
  - os_process_vs_thread: "Because each process has its own memory space, communication between processes usually requires inter-process communication mechanisms"

*Notes:* Preserve usually (convention C4).

## v3_015 · exact_term · answer

**Q:** Which four counts does a confusion matrix summarize?

**Reference:** True positives, true negatives, false positives and false negatives.
- `four_counts`: True positives, true negatives, false positives and false negatives.
  - ml_model_evaluation: "A confusion matrix summarizes classification results using true positives, true negatives, false positives, and false negatives."

*Notes:* All four are needed for the point.

## v3_016 · exact_term · answer

**Q:** In k-fold cross-validation, how many times does each subset serve as the validation set?

**Reference:** Once.
- `once`: Each subset serves as the validation set once.
  - ml_cross_validation: "Each subset serves as the validation set once."

*Notes:* Short factual lookup.

## v3_017 · exact_term · answer

**Q:** What does recall measure for a classifier?

**Reference:** How many actual positive instances are correctly identified.
- `recall`: Recall measures how many actual positive instances are correctly identified.
  - ml_model_evaluation: "Recall measures how many actual positive instances are correctly identified."

*Notes:* Must not be confused with precision.

## v3_018 · exact_term · answer

**Q:** Which CPU scheduling algorithms are listed as common?

**Reference:** First-come first-served, shortest job first, priority scheduling and round robin.
- `algorithms`: First-come first-served, shortest job first, priority scheduling and round robin.
  - os_processes_threads_scheduling: "Common scheduling algorithms include first-come first-served, shortest job first, priority scheduling, and round robin."

*Notes:* All four are needed for the point.

## v3_019 · cross_note · answer

**Q:** How does regularization help, and which other techniques can help reduce overfitting?

**Reference:** Regularization can reduce variance by discouraging overly complex models. Cross-validation and collecting more data can also help reduce overfitting.
- `reduces_variance`: Regularization can reduce variance by discouraging overly complex models.
  - ml_bias_variance_generalization: "Regularization can reduce variance by discouraging overly complex models."
- `other_techniques`: Cross-validation and collecting more data can also help reduce overfitting.
  - ml_overfitting_underfitting: "Techniques such as regularization, cross-validation, and collecting more data can help reduce overfitting."

*Notes:* Needs both notes. Preserve can.

## v3_020 · cross_note · answer

**Q:** How are bias and variance related to underfitting and overfitting?

**Reference:** High-bias models are usually too simple and may underfit; high-variance models may fit noise in the training data and overfit.
- `bias_underfit`: High-bias models are usually too simple and may underfit.
  - ml_bias_variance_generalization: "High-bias models are usually too simple and may underfit the training data."
  - ml_overfitting_underfitting: "Underfit models typically have high bias"
- `variance_overfit`: High-variance models may fit noise in the training set and therefore overfit.
  - ml_bias_variance_generalization: "High-variance models may fit noise in the training set and therefore overfit."

*Notes:* Preserve usually and may.

## v3_021 · cross_note · answer

**Q:** What is the difference between normalization in databases and normalization of features?

**Reference:** Database normalization organizes relational data to reduce redundancy and improve integrity; feature normalization rescales values to a specific range.
- `database`: In databases, normalization organizes data to reduce redundancy and improve data integrity.
  - db_normalization_intro: "Normalization is the process of organizing data in a relational database to reduce redundancy and improve data integrity."
- `features`: For features, normalization rescales values to a specific range.
  - ml_feature_engineering: "Normalization rescales values to a specific range."

*Notes:* Ambiguous term across notes: retrieval must find both.

## v3_022 · cross_note · answer

**Q:** What signs of overfitting do the notes describe?

**Reference:** Overfit models often perform well on training data but poorly on unseen data, and a gap between training and validation accuracy is often a sign of overfitting.
- `train_vs_unseen`: Performing well on training data but poorly on unseen or test data.
  - ml_overfitting_underfitting: "Overfit models often perform well on training data but poorly on unseen data."
  - ml_supervised_learning_basics: "A model that performs very well on training data but poorly on test data is said to be overfitting."
- `accuracy_gap`: A gap between training accuracy and validation accuracy is often a sign of overfitting.
  - ml_bias_variance_generalization: "A gap between training accuracy and validation accuracy is often a sign of overfitting."

*Notes:* Preserve often.

## v3_023 · cross_note · answer

**Q:** What role does cross-validation play in evaluating a model?

**Reference:** It estimates how well a model is likely to perform on unseen data and is often used to obtain a more reliable estimate of model performance.
- `estimate_unseen`: It estimates how well a model is likely to perform on unseen data (its generalization performance).
  - ml_bias_variance_generalization: "Cross-validation is used to estimate how well a model is likely to perform on unseen data."
  - ml_cross_validation: "It is commonly used to estimate model generalization performance."
- `more_reliable`: It is often used to obtain a more reliable estimate of model performance.
  - ml_model_evaluation: "Cross-validation is often used to obtain a more reliable estimate of model performance."

*Notes:* Evidence spread over three notes.

## v3_024 · cross_note · answer

**Q:** Why do threads communicate more easily than processes, and what risk does that bring?

**Reference:** Threads share memory, so they communicate more easily, but this introduces risks such as race conditions and synchronization problems.
- `shared_memory`: Threads of the same process share memory.
  - os_process_vs_thread: "Threads communicate more easily because they share memory."
  - os_processes_threads_scheduling: "Threads of the same process share memory and resources, which makes communication between them faster"
- `risk`: It introduces risks such as race conditions and synchronization problems.
  - os_process_vs_thread: "it also introduces risks such as race conditions and synchronization problems"
  - os_processes_threads_scheduling: "also introduces synchronization issues"

*Notes:* Either note supports each point.

## v3_025 · multi_part · answer

**Q:** Which three kinds of anomalies can poorly designed tables cause, and what is a deletion anomaly?

**Reference:** Update, insertion and deletion anomalies. A deletion anomaly happens when removing one row accidentally removes other valuable information.
- `three_anomalies`: Update, insertion and deletion anomalies.
  - db_normalization_intro: "which can cause update anomalies, insertion anomalies, and deletion anomalies"
- `deletion`: A deletion anomaly happens when removing one row accidentally removes other valuable information.
  - db_normalization_intro: "A deletion anomaly happens when removing one row accidentally removes other valuable information."

*Notes:* Both parts required.

## v3_026 · multi_part · answer

**Q:** What is a transaction, and what does consistency mean in ACID?

**Reference:** A logical unit of work that either completes entirely or has no effect; consistency means the database moves from one valid state to another.
- `transaction`: A transaction is a logical unit of work that must either complete entirely or have no effect at all.
  - db_transactions_concurrency: "A transaction is a logical unit of work that must either complete entirely or have no effect at all."
- `consistency`: Consistency means the database moves from one valid state to another valid state.
  - db_transactions_concurrency: "Consistency means the database moves from one valid state to another valid state."

*Notes:* Both parts required.

## v3_027 · multi_part · answer

**Q:** What is feature scaling for, and how do normalization and standardization differ?

**Reference:** Feature scaling places features on comparable ranges. Normalization rescales values to a specific range; standardization gives them zero mean and unit variance.
- `scaling`: Feature scaling places features on comparable ranges.
  - ml_feature_engineering: "Feature scaling is commonly used to place features on comparable ranges."
- `normalization`: Normalization rescales values to a specific range.
  - ml_feature_engineering: "Normalization rescales values to a specific range."
- `standardization`: Standardization transforms values to zero mean and unit variance.
  - ml_feature_engineering: "Standardization transforms values so they have zero mean and unit variance."

*Notes:* Three points. Must not mix in database normalization.

## v3_028 · multi_part · answer

**Q:** What is the goal of supervised learning, and what does the model minimize during training?

**Reference:** To learn a mapping from inputs to outputs that generalizes to unseen data; it minimizes a loss function measuring the difference between predictions and true labels.
- `goal`: To learn a mapping from inputs to outputs that generalizes to unseen data.
  - ml_supervised_learning_basics: "The goal is to learn a mapping from inputs to outputs so that the model can generalize to unseen data."
- `loss`: A loss function measuring the difference between predictions and true labels.
  - ml_supervised_learning_basics: "During training, the model minimizes a loss function that measures the difference between predictions and true labels."

*Notes:* Both parts required.

## v3_029 · multi_part · answer

**Q:** What is multithreading useful for, and which two examples are given?

**Reference:** Applications that perform multiple tasks concurrently, such as a web server handling many client requests or a program doing background work while keeping its interface responsive.
- `concurrent_tasks`: Applications that perform multiple tasks concurrently.
  - os_process_vs_thread: "Multithreading is useful for applications that perform multiple tasks concurrently"
- `examples`: A web server handling multiple client requests, and a program doing background work while keeping the user interface responsive.
  - os_process_vs_thread: "such as a web server handling multiple client requests or a program performing background work while keeping the user interface responsive"

*Notes:* Both examples are needed for the examples point.

## v3_030 · multi_part · answer

**Q:** What is the difference between training error and test error?

**Reference:** Training error is performance on the training set; test error is performance on new, unseen data.
- `training_error`: Training error refers to performance on the training set.
  - ml_supervised_learning_basics: "Training error refers to performance on the training set"
- `test_error`: Test error refers to performance on new unseen data.
  - ml_supervised_learning_basics: "test error refers to performance on new unseen data"

*Notes:* Both parts required.

## v3_031 · qualifier · answer

**Q:** Does a learning rate that is too large always make gradient descent diverge?

**Reference:** The notes say it may cause divergence; they do not say it always does.
- `may_not_always`: No: the notes say a learning rate that is too large may cause divergence, not that it always does.
  - ml_gradient_descent: "A learning rate that is too large may cause divergence."

*Notes:* Answering 'yes, always' fails groundedness and correctness (C4).

## v3_032 · qualifier · answer

**Q:** Do good features always improve a model more than making it more complex?

**Reference:** The notes say good features often, not always, improve performance more than increasing model complexity.
- `often`: Not always: good features often improve performance more than increasing model complexity.
  - ml_feature_engineering: "Good features often improve model performance more than increasing model complexity."

*Notes:* Preserve often (C4).

## v3_033 · qualifier · answer

**Q:** Are high-bias models always too simple?

**Reference:** The notes say high-bias models are usually too simple and may underfit, not always.
- `usually`: Not always: high-bias models are usually too simple and may underfit.
  - ml_bias_variance_generalization: "High-bias models are usually too simple and may underfit the training data."

*Notes:* Preserve usually and may (C4).

## v3_034 · qualifier · answer

**Q:** Is decomposition always required to fix a transitive dependency?

**Reference:** The notes say decomposition is often used to split such a table; they do not say it is always required.
- `often_used`: The notes say decomposition is often used for such tables; they do not say it is always required.
  - db_normalization_intro: "Decomposition is often used to split such a table into smaller relations while preserving data meaning."

*Notes:* Preserve often (C4). Claiming it is required is unsupported.

## v3_035 · near_miss_refusal · refuse

**Q:** What is the mathematical formula for precision?

**Reference:** I don't know.
- Closest the notes come:
  - ml_model_evaluation: "Precision measures how many predicted positive instances are actually positive."

*Notes:* Precision is defined in words only; no formula is given.

## v3_036 · near_miss_refusal · refuse

**Q:** What value of k is usually chosen for k-fold cross-validation?

**Reference:** I don't know.
- Closest the notes come:
  - ml_cross_validation: "K-fold cross-validation divides data into k subsets."

*Notes:* No value of k is given.

## v3_037 · near_miss_refusal · refuse

**Q:** How long should the time quantum be in round robin scheduling?

**Reference:** I don't know.
- Closest the notes come:
  - os_processes_threads_scheduling: "Round robin assigns each process a fixed time quantum"

*Notes:* The quantum is mentioned but no length is given.

## v3_038 · near_miss_refusal · refuse

**Q:** What learning rate value should I start with?

**Reference:** I don't know.
- Closest the notes come:
  - ml_gradient_descent: "The learning rate controls the size of parameter updates."

*Notes:* No recommended value is given.

## v3_039 · near_miss_refusal · refuse

**Q:** What does the fourth normal form remove?

**Reference:** I don't know.
- Closest the notes come:
  - db_normalization_intro: "The third normal form removes transitive dependency"

*Notes:* Only the first three normal forms are covered.

## v3_040 · near_miss_refusal · refuse

**Q:** How does shortest job first decide which process runs next?

**Reference:** I don't know.
- Closest the notes come:
  - os_processes_threads_scheduling: "Common scheduling algorithms include first-come first-served, shortest job first, priority scheduling, and round robin."

*Notes:* Shortest job first is named but its rule is not described. Explaining it from the name is outside knowledge.

## v3_041 · near_miss_refusal · refuse

**Q:** Which transaction isolation levels do SQL databases offer?

**Reference:** I don't know.
- Closest the notes come:
  - db_transactions_concurrency: "Isolation means concurrent transactions should not interfere in a way that produces incorrect results."

*Notes:* Isolation is defined, but no isolation levels are listed.

## v3_042 · near_miss_refusal · refuse

**Q:** How does multiversion concurrency control work internally?

**Reference:** I don't know.
- Closest the notes come:
  - db_transactions_concurrency: "Locking and multiversion concurrency control are two common approaches to handling concurrency."

*Notes:* Named only; no mechanism.

## v3_043 · near_miss_refusal · refuse

**Q:** What is the difference between L1 and L2 regularization?

**Reference:** I don't know.
- Closest the notes come:
  - ml_bias_variance_generalization: "Regularization can reduce variance by discouraging overly complex models."

*Notes:* Regularization is covered, but no types of it.

## v3_044 · near_miss_refusal · refuse

**Q:** How does a race condition happen, step by step?

**Reference:** I don't know.
- Closest the notes come:
  - os_process_vs_thread: "it also introduces risks such as race conditions and synchronization problems"

*Notes:* Race conditions are named as a risk only.

## v3_045 · out_of_scope · refuse

**Q:** How does backpropagation compute gradients in a neural network?

**Reference:** I don't know.
- Closest the notes come:
  - ml_gradient_descent: "Gradient descent is a fundamental component of many machine learning algorithms and neural networks."

*Notes:* Neural networks are mentioned in passing; backpropagation is not covered.

## v3_046 · out_of_scope · refuse

**Q:** Who proposed the relational model of data?

**Reference:** I don't know.

*Notes:* No history is covered.

## v3_047 · out_of_scope · refuse

**Q:** How does a B-tree index speed up queries?

**Reference:** I don't know.

*Notes:* Indexing is not covered.

## v3_048 · out_of_scope · refuse

**Q:** What happens during a page fault in virtual memory?

**Reference:** I don't know.

*Notes:* Memory management is not covered.
