# v3 held-out review: labelling sheet

Label each answer in `v3_human_review_sample.json` (fields under `labels`). The judge's verdicts are hidden on purpose.

| Label | Meaning |
|---|---|
| `correctness` | 1 if every claim is accurate according to the notes, 0 if any claim is wrong or cannot be validated, N/A for a pure refusal |
| `groundedness` | 1 if every claim follows from the supplied sources, 0 if anything is added (including a dropped may/usually/often) |
| `citation_correctness` | 1 if every claim has a citation to a source that supports it (a trailing citation may cover a short paragraph), else 0; N/A for a pure refusal |
| `refusal_correctness` | N/A when an answerable question was answered; otherwise 1 for a justified refusal, 0 for a wrong one |
| `points` | pass or fail for each required point |

## v3_001

**Q:** What can happen when the steps an optimizer takes are far too small?

**Sources the model saw:**

- [S1] *ml_gradient_descent*: Gradient descent is an optimization algorithm used to minimize a loss function. The algorithm updates model parameters in the direction that reduces prediction error. The learning rate controls the size of parameter updates. A learning rate that is too large may cause divergence. A learning rate that is too small may result in slow convergence. Gradient descent is a fundamental component of many machine learning algorithms and neural networks.
- [S2] *ml_overfitting_underfitting*: Underfitting occurs when a model is too simple to capture patterns in the training data. Underfit models typically have high bias and poor performance on both training and test data. Overfitting occurs when a model learns noise and specific details of the training data instead of general patterns. Overfit models often perform well on training data but poorly on unseen data. Model complexity influences the balance between underfitting and overfitting.
- [S3] *ml_overfitting_underfitting*: Underfitting occurs when a model is too simple to capture patterns in the training data. Underfit models typically have high bias and poor performance on both training and test data. Overfitting occurs when a model learns noise and specific details of the training data instead of general patterns. Overfit models often perform well on training data but poorly on unseen data. Model complexity influences the balance between underfitting and overfitting. Techniques such as regularization, cross-validation, and collecting more data can help reduce overfitting. The bias-variance tradeoff explains the relationship between model complexity and generalization performance.
- [S4] *ml_bias_variance_generalization*: The bias-variance tradeoff helps explain prediction error in machine learning models. Bias refers to error caused by overly simplistic assumptions in the learning algorithm. High-bias models are usually too simple and may underfit the training data. Variance refers to error caused by excessive sensitivity to the training data. High-variance models may fit noise in the training set and therefore overfit. Good generalization requires balancing these two sources of error. Increasing model complexity can reduce bias but may increase variance. Regularization can reduce variance by discouraging overly complex models. Cross-validation is used to estimate how well a model is likely to perform on unseen data. In k-fold cross-validation, the dataset is divided into k subsets, and the model is trained multiple times, each time leaving out one subset for validation. A gap between training accuracy and validation accuracy is often a sign of overfitting.
- [S5] *ml_bias_variance_generalization*: The bias-variance tradeoff helps explain prediction error in machine learning models. Bias refers to error caused by overly simplistic assumptions in the learning algorithm. High-bias models are usually too simple and may underfit the training data. Variance refers to error caused by excessive sensitivity to the training data. High-variance models may fit noise in the training set and therefore overfit. Good generalization requires balancing these two sources of error.

**Answer:** A learning rate that is too small may result in slow convergence [S1].

**Required points:**
- `slow_convergence`: A learning rate that is too small may result in slow convergence.

*Reference:* If the learning rate (step size) is too small, gradient descent may converge slowly.  
*Case notes:* Preserve may. The question never says learning rate or convergence.

## v3_003

**Q:** Which transformation makes every input have an average of zero and a spread of one?

**Sources the model saw:**

- [S1] *ml_feature_engineering*: Features are the inputs used by a machine learning model. Feature engineering is the process of selecting, transforming, and creating useful features from raw data. Feature scaling is commonly used to place features on comparable ranges. Normalization rescales values to a specific range. Standardization transforms values so they have zero mean and unit variance. Good features often improve model performance more than increasing model complexity.
- [S2] *db_normalization_intro*: Normalization is the process of organizing data in a relational database to reduce redundancy and improve data integrity. Poorly designed tables often repeat the same facts in multiple rows, which can cause update anomalies, insertion anomalies, and deletion anomalies. An update anomaly happens when the same fact must be changed in several places and some copies are missed. An insertion anomaly happens when a new fact cannot be inserted without adding unrelated data. A deletion anomaly happens when removing one row accidentally removes other valuable information. The first normal form requires that each attribute contain atomic values and that there are no repeating groups. The second normal form removes partial dependency, meaning that non-key attributes must depend on the whole primary key rather than just part of a composite key. The third normal form removes transitive dependency, so non-key attributes should not depend on other non-key attributes.
- [S3] *db_normalization_intro*: Normalization is the process of organizing data in a relational database to reduce redundancy and improve data integrity. Poorly designed tables often repeat the same facts in multiple rows, which can cause update anomalies, insertion anomalies, and deletion anomalies. An update anomaly happens when the same fact must be changed in several places and some copies are missed. An insertion anomaly happens when a new fact cannot be inserted without adding unrelated data.
- [S4] *os_processes_threads_scheduling*: A process is an executing program with its own memory space, resources, and execution state. A thread is a smaller unit of execution within a process. Threads of the same process share memory and resources, which makes communication between them faster but also introduces synchronization issues. Context switching between processes is generally more expensive than switching between threads because more state must be saved and restored. CPU scheduling determines which ready process or thread gets access to the processor. Common scheduling algorithms include first-come first-served, shortest job first, priority scheduling, and round robin. First-come first-served is simple but can produce poor average waiting time. Round robin assigns each process a fixed time quantum and cycles through ready tasks, which improves responsiveness in time-sharing systems. Starvation can occur when lower-priority tasks wait indefinitely.
- [S5] *ml_supervised_learning_basics*: Supervised learning is a machine learning paradigm in which a model learns from labeled examples. Each training example contains input features and a target output. The goal is to learn a mapping from inputs to outputs so that the model can generalize to unseen data. Supervised learning tasks are often divided into classification and regression. Classification predicts discrete categories, such as whether an email is spam or not spam.

**Answer:** Standardization transforms values so they have zero mean and unit variance [S1].

**Required points:**
- `standardization`: Standardization transforms values to zero mean and unit variance.

*Reference:* Standardization, which transforms values to have zero mean and unit variance.  
*Case notes:* Must not answer normalization, which rescales to a range.

## v3_005

**Q:** Two people edit the same record at the same time and one person's change silently disappears. What is this called?

**Sources the model saw:**

- [S1] *db_transactions_concurrency*: Durability means that once a transaction is committed, its effects persist even after a crash. Concurrency control is needed because many users may access the same data at the same time. Problems that can appear without proper control include lost updates, dirty reads, and non-repeatable reads. A lost update occurs when one transaction overwrites the result of another. A dirty read happens when a transaction reads data written by another transaction that has not yet committed. A non-repeatable read occurs when the same query returns different results within a single transaction because another transaction modified the data in the meantime. Locking and multiversion concurrency control are two common approaches to handling concurrency.
- [S2] *db_transactions_concurrency*: A transaction is a logical unit of work that must either complete entirely or have no effect at all. The ACID properties describe the reliability of transactions. Atomicity means all operations of a transaction happen or none happen. Consistency means the database moves from one valid state to another valid state. Isolation means concurrent transactions should not interfere in a way that produces incorrect results. Durability means that once a transaction is committed, its effects persist even after a crash. Concurrency control is needed because many users may access the same data at the same time. Problems that can appear without proper control include lost updates, dirty reads, and non-repeatable reads. A lost update occurs when one transaction overwrites the result of another. A dirty read happens when a transaction reads data written by another transaction that has not yet committed.
- [S3] *db_normalization_intro*: Normalization is the process of organizing data in a relational database to reduce redundancy and improve data integrity. Poorly designed tables often repeat the same facts in multiple rows, which can cause update anomalies, insertion anomalies, and deletion anomalies. An update anomaly happens when the same fact must be changed in several places and some copies are missed. An insertion anomaly happens when a new fact cannot be inserted without adding unrelated data. A deletion anomaly happens when removing one row accidentally removes other valuable information. The first normal form requires that each attribute contain atomic values and that there are no repeating groups. The second normal form removes partial dependency, meaning that non-key attributes must depend on the whole primary key rather than just part of a composite key. The third normal form removes transitive dependency, so non-key attributes should not depend on other non-key attributes.
- [S4] *os_processes_threads_scheduling*: A process is an executing program with its own memory space, resources, and execution state. A thread is a smaller unit of execution within a process. Threads of the same process share memory and resources, which makes communication between them faster but also introduces synchronization issues. Context switching between processes is generally more expensive than switching between threads because more state must be saved and restored. CPU scheduling determines which ready process or thread gets access to the processor. Common scheduling algorithms include first-come first-served, shortest job first, priority scheduling, and round robin. First-come first-served is simple but can produce poor average waiting time. Round robin assigns each process a fixed time quantum and cycles through ready tasks, which improves responsiveness in time-sharing systems. Starvation can occur when lower-priority tasks wait indefinitely.
- [S5] *db_normalization_intro*: Normalization is the process of organizing data in a relational database to reduce redundancy and improve data integrity. Poorly designed tables often repeat the same facts in multiple rows, which can cause update anomalies, insertion anomalies, and deletion anomalies. An update anomaly happens when the same fact must be changed in several places and some copies are missed. An insertion anomaly happens when a new fact cannot be inserted without adding unrelated data.

**Answer:** This is called a lost update [S1].

**Required points:**
- `lost_update`: This is a lost update: one transaction overwrites the result of another.

*Reference:* A lost update, where one transaction overwrites the result of another.  
*Case notes:* Name and mechanism both required.

## v3_006

**Q:** Why is switching between two separate running programs slower than switching between two workers inside the same program?

**Sources the model saw:**

- [S1] *os_processes_threads_scheduling*: A process is an executing program with its own memory space, resources, and execution state. A thread is a smaller unit of execution within a process. Threads of the same process share memory and resources, which makes communication between them faster but also introduces synchronization issues. Context switching between processes is generally more expensive than switching between threads because more state must be saved and restored. CPU scheduling determines which ready process or thread gets access to the processor. Common scheduling algorithms include first-come first-served, shortest job first, priority scheduling, and round robin. First-come first-served is simple but can produce poor average waiting time. Round robin assigns each process a fixed time quantum and cycles through ready tasks, which improves responsiveness in time-sharing systems. Starvation can occur when lower-priority tasks wait indefinitely.
- [S2] *os_processes_threads_scheduling*: A process is an executing program with its own memory space, resources, and execution state. A thread is a smaller unit of execution within a process. Threads of the same process share memory and resources, which makes communication between them faster but also introduces synchronization issues. Context switching between processes is generally more expensive than switching between threads because more state must be saved and restored.
- [S3] *os_process_vs_thread*: Because each process has its own memory space, communication between processes usually requires inter-process communication mechanisms such as pipes, sockets, or shared memory. Threads communicate more easily because they share memory. This makes threads more efficient for tasks that need frequent communication, but it also introduces risks such as race conditions and synchronization problems. Creating and switching between processes is generally more expensive than creating and switching between threads because processes require more operating system overhead. Multithreading is useful for applications that perform multiple tasks concurrently, such as a web server handling multiple client requests or a program performing background work while keeping the user interface responsive. A process can contain one thread or multiple threads.
- [S4] *os_process_vs_thread*: Creating and switching between processes is generally more expensive than creating and switching between threads because processes require more operating system overhead. Multithreading is useful for applications that perform multiple tasks concurrently, such as a web server handling multiple client requests or a program performing background work while keeping the user interface responsive. A process can contain one thread or multiple threads. If a process has only one thread, it is called single-threaded. If it has multiple threads, it is called multithreaded. In summary, a process provides isolation and resource ownership, while a thread provides a lightweight path of execution within a process.
- [S5] *os_process_vs_thread*: A process is an independent program in execution. Each process has its own memory space, resources, and execution state. A thread is the smallest unit of execution within a process. Threads that belong to the same process share the same memory space and resources, but each thread has its own stack and program counter. Processes are more isolated than threads.

**Answer:** Context switching between processes is generally more expensive than switching between threads because more state must be saved and restored for processes [S1].

**Required points:**
- `more_expensive`: Switching between processes is generally more expensive than switching between threads.
- `reason`: Because more state must be saved and restored (more operating system overhead).

*Reference:* Switching between processes is generally more expensive than switching between threads, because more state must be saved and restored and processes require more operating-system overhead.  
*Case notes:* Either reason satisfies the reason point. Preserve generally.

## v3_007

**Q:** What do you call a model that is too simple and does badly even on the data it learned from?

**Sources the model saw:**

- [S1] *ml_overfitting_underfitting*: Underfitting occurs when a model is too simple to capture patterns in the training data. Underfit models typically have high bias and poor performance on both training and test data. Overfitting occurs when a model learns noise and specific details of the training data instead of general patterns. Overfit models often perform well on training data but poorly on unseen data. Model complexity influences the balance between underfitting and overfitting.
- [S2] *ml_overfitting_underfitting*: Underfitting occurs when a model is too simple to capture patterns in the training data. Underfit models typically have high bias and poor performance on both training and test data. Overfitting occurs when a model learns noise and specific details of the training data instead of general patterns. Overfit models often perform well on training data but poorly on unseen data. Model complexity influences the balance between underfitting and overfitting. Techniques such as regularization, cross-validation, and collecting more data can help reduce overfitting. The bias-variance tradeoff explains the relationship between model complexity and generalization performance.
- [S3] *ml_supervised_learning_basics*: Regression predicts continuous values, such as the price of a house. During training, the model minimizes a loss function that measures the difference between predictions and true labels. Training error refers to performance on the training set, while test error refers to performance on new unseen data. A model that performs very well on training data but poorly on test data is said to be overfitting. A model that performs poorly even on training data may be underfitting. Feature selection, regularization, and cross-validation are common techniques used to improve generalization.
- [S4] *ml_bias_variance_generalization*: The bias-variance tradeoff helps explain prediction error in machine learning models. Bias refers to error caused by overly simplistic assumptions in the learning algorithm. High-bias models are usually too simple and may underfit the training data. Variance refers to error caused by excessive sensitivity to the training data. High-variance models may fit noise in the training set and therefore overfit. Good generalization requires balancing these two sources of error. Increasing model complexity can reduce bias but may increase variance. Regularization can reduce variance by discouraging overly complex models. Cross-validation is used to estimate how well a model is likely to perform on unseen data. In k-fold cross-validation, the dataset is divided into k subsets, and the model is trained multiple times, each time leaving out one subset for validation. A gap between training accuracy and validation accuracy is often a sign of overfitting.
- [S5] *ml_supervised_learning_basics*: Supervised learning is a machine learning paradigm in which a model learns from labeled examples. Each training example contains input features and a target output. The goal is to learn a mapping from inputs to outputs so that the model can generalize to unseen data. Supervised learning tasks are often divided into classification and regression. Classification predicts discrete categories, such as whether an email is spam or not spam. Regression predicts continuous values, such as the price of a house. During training, the model minimizes a loss function that measures the difference between predictions and true labels. Training error refers to performance on the training set, while test error refers to performance on new unseen data. A model that performs very well on training data but poorly on test data is said to be overfitting. A model that performs poorly even on training data may be underfitting.

**Answer:** A model that is too simple and does badly even on the data it learned from is called underfitting [S1].

**Required points:**
- `underfitting`: This is underfitting: the model is too simple to capture patterns in the training data.

*Reference:* Underfitting: the model is too simple to capture the patterns in the training data, so it performs poorly even there.  
*Case notes:* Naming underfitting with its meaning is required.

## v3_008

**Q:** What is it called when one large table is split into several smaller ones while keeping what the data means?

**Sources the model saw:**

- [S1] *db_normalization_intro*: A deletion anomaly happens when removing one row accidentally removes other valuable information. The first normal form requires that each attribute contain atomic values and that there are no repeating groups. The second normal form removes partial dependency, meaning that non-key attributes must depend on the whole primary key rather than just part of a composite key. The third normal form removes transitive dependency, so non-key attributes should not depend on other non-key attributes. For example, if a student table stores department_name and department_office, and department_office depends on department_name rather than student_id, then the design has a transitive dependency. Decomposition is often used to split such a table into smaller relations while preserving data meaning.
- [S2] *ml_cross_validation*: Cross-validation evaluates model performance by repeatedly splitting data into training and validation sets. K-fold cross-validation divides data into k subsets. Each subset serves as the validation set once. Cross-validation reduces the risk of relying on a single train-test split. It is commonly used to estimate model generalization performance.
- [S3] *db_normalization_intro*: Normalization is the process of organizing data in a relational database to reduce redundancy and improve data integrity. Poorly designed tables often repeat the same facts in multiple rows, which can cause update anomalies, insertion anomalies, and deletion anomalies. An update anomaly happens when the same fact must be changed in several places and some copies are missed. An insertion anomaly happens when a new fact cannot be inserted without adding unrelated data.
- [S4] *db_normalization_intro*: Normalization is the process of organizing data in a relational database to reduce redundancy and improve data integrity. Poorly designed tables often repeat the same facts in multiple rows, which can cause update anomalies, insertion anomalies, and deletion anomalies. An update anomaly happens when the same fact must be changed in several places and some copies are missed. An insertion anomaly happens when a new fact cannot be inserted without adding unrelated data. A deletion anomaly happens when removing one row accidentally removes other valuable information. The first normal form requires that each attribute contain atomic values and that there are no repeating groups. The second normal form removes partial dependency, meaning that non-key attributes must depend on the whole primary key rather than just part of a composite key. The third normal form removes transitive dependency, so non-key attributes should not depend on other non-key attributes.
- [S5] *db_transactions_concurrency*: Durability means that once a transaction is committed, its effects persist even after a crash. Concurrency control is needed because many users may access the same data at the same time. Problems that can appear without proper control include lost updates, dirty reads, and non-repeatable reads. A lost update occurs when one transaction overwrites the result of another. A dirty read happens when a transaction reads data written by another transaction that has not yet committed. A non-repeatable read occurs when the same query returns different results within a single transaction because another transaction modified the data in the meantime. Locking and multiversion concurrency control are two common approaches to handling concurrency.

**Answer:** Decomposition. [S1]

**Required points:**
- `decomposition`: Decomposition splits a table into smaller relations while preserving data meaning.

*Reference:* Decomposition, which splits a table into smaller relations while preserving data meaning.  
*Case notes:* The question avoids the words relation, decompose and normalization.

## v3_010

**Q:** Which way of sharing the processor gives every task a fixed slice of time in turn, and what does that improve?

**Sources the model saw:**

- [S1] *os_processes_threads_scheduling*: CPU scheduling determines which ready process or thread gets access to the processor. Common scheduling algorithms include first-come first-served, shortest job first, priority scheduling, and round robin. First-come first-served is simple but can produce poor average waiting time. Round robin assigns each process a fixed time quantum and cycles through ready tasks, which improves responsiveness in time-sharing systems. Starvation can occur when lower-priority tasks wait indefinitely. Aging is a technique used to gradually increase the priority of waiting tasks in order to reduce starvation. The distinction between process and thread is important for performance, isolation, and system design.
- [S2] *os_processes_threads_scheduling*: A process is an executing program with its own memory space, resources, and execution state. A thread is a smaller unit of execution within a process. Threads of the same process share memory and resources, which makes communication between them faster but also introduces synchronization issues. Context switching between processes is generally more expensive than switching between threads because more state must be saved and restored. CPU scheduling determines which ready process or thread gets access to the processor. Common scheduling algorithms include first-come first-served, shortest job first, priority scheduling, and round robin. First-come first-served is simple but can produce poor average waiting time. Round robin assigns each process a fixed time quantum and cycles through ready tasks, which improves responsiveness in time-sharing systems. Starvation can occur when lower-priority tasks wait indefinitely.
- [S3] *db_transactions_concurrency*: A transaction is a logical unit of work that must either complete entirely or have no effect at all. The ACID properties describe the reliability of transactions. Atomicity means all operations of a transaction happen or none happen. Consistency means the database moves from one valid state to another valid state. Isolation means concurrent transactions should not interfere in a way that produces incorrect results. Durability means that once a transaction is committed, its effects persist even after a crash. Concurrency control is needed because many users may access the same data at the same time. Problems that can appear without proper control include lost updates, dirty reads, and non-repeatable reads. A lost update occurs when one transaction overwrites the result of another. A dirty read happens when a transaction reads data written by another transaction that has not yet committed.
- [S4] *os_processes_threads_scheduling*: A process is an executing program with its own memory space, resources, and execution state. A thread is a smaller unit of execution within a process. Threads of the same process share memory and resources, which makes communication between them faster but also introduces synchronization issues. Context switching between processes is generally more expensive than switching between threads because more state must be saved and restored.
- [S5] *db_transactions_concurrency*: A transaction is a logical unit of work that must either complete entirely or have no effect at all. The ACID properties describe the reliability of transactions. Atomicity means all operations of a transaction happen or none happen. Consistency means the database moves from one valid state to another valid state. Isolation means concurrent transactions should not interfere in a way that produces incorrect results.

**Answer:** Round robin scheduling gives every task a fixed slice of time in turn, and it improves responsiveness in time-sharing systems [S1].

**Required points:**
- `round_robin`: Round robin assigns each process a fixed time quantum and cycles through ready tasks.
- `responsiveness`: It improves responsiveness in time-sharing systems.

*Reference:* Round robin: each process gets a fixed time quantum in turn, which improves responsiveness in time-sharing systems.  
*Case notes:* Both parts required.

## v3_017

**Q:** What does recall measure for a classifier?

**Sources the model saw:**

- [S1] *ml_model_evaluation*: Model evaluation measures how well a machine learning model performs on unseen data. A model should not only fit the training data but also generalize to new examples. A confusion matrix summarizes classification results using true positives, true negatives, false positives, and false negatives. Accuracy measures the proportion of correct predictions. Accuracy can be misleading on imbalanced datasets. Precision measures how many predicted positive instances are actually positive. Recall measures how many actual positive instances are correctly identified. The F1 score combines precision and recall into a single metric and is useful when both are important. Cross-validation is often used to obtain a more reliable estimate of model performance.
- [S2] *ml_supervised_learning_basics*: Regression predicts continuous values, such as the price of a house. During training, the model minimizes a loss function that measures the difference between predictions and true labels. Training error refers to performance on the training set, while test error refers to performance on new unseen data. A model that performs very well on training data but poorly on test data is said to be overfitting. A model that performs poorly even on training data may be underfitting. Feature selection, regularization, and cross-validation are common techniques used to improve generalization.
- [S3] *ml_supervised_learning_basics*: Supervised learning is a machine learning paradigm in which a model learns from labeled examples. Each training example contains input features and a target output. The goal is to learn a mapping from inputs to outputs so that the model can generalize to unseen data. Supervised learning tasks are often divided into classification and regression. Classification predicts discrete categories, such as whether an email is spam or not spam.
- [S4] *ml_supervised_learning_basics*: Supervised learning is a machine learning paradigm in which a model learns from labeled examples. Each training example contains input features and a target output. The goal is to learn a mapping from inputs to outputs so that the model can generalize to unseen data. Supervised learning tasks are often divided into classification and regression. Classification predicts discrete categories, such as whether an email is spam or not spam. Regression predicts continuous values, such as the price of a house. During training, the model minimizes a loss function that measures the difference between predictions and true labels. Training error refers to performance on the training set, while test error refers to performance on new unseen data. A model that performs very well on training data but poorly on test data is said to be overfitting. A model that performs poorly even on training data may be underfitting.
- [S5] *ml_model_evaluation*: Model evaluation measures how well a machine learning model performs on unseen data. A model should not only fit the training data but also generalize to new examples. A confusion matrix summarizes classification results using true positives, true negatives, false positives, and false negatives. Accuracy measures the proportion of correct predictions. Accuracy can be misleading on imbalanced datasets. Precision measures how many predicted positive instances are actually positive.

**Answer:** Recall measures how many actual positive instances are correctly identified [S1].

**Required points:**
- `recall`: Recall measures how many actual positive instances are correctly identified.

*Reference:* How many actual positive instances are correctly identified.  
*Case notes:* Must not be confused with precision.

## v3_018

**Q:** Which CPU scheduling algorithms are listed as common?

**Sources the model saw:**

- [S1] *os_processes_threads_scheduling*: CPU scheduling determines which ready process or thread gets access to the processor. Common scheduling algorithms include first-come first-served, shortest job first, priority scheduling, and round robin. First-come first-served is simple but can produce poor average waiting time. Round robin assigns each process a fixed time quantum and cycles through ready tasks, which improves responsiveness in time-sharing systems. Starvation can occur when lower-priority tasks wait indefinitely. Aging is a technique used to gradually increase the priority of waiting tasks in order to reduce starvation. The distinction between process and thread is important for performance, isolation, and system design.
- [S2] *os_processes_threads_scheduling*: A process is an executing program with its own memory space, resources, and execution state. A thread is a smaller unit of execution within a process. Threads of the same process share memory and resources, which makes communication between them faster but also introduces synchronization issues. Context switching between processes is generally more expensive than switching between threads because more state must be saved and restored. CPU scheduling determines which ready process or thread gets access to the processor. Common scheduling algorithms include first-come first-served, shortest job first, priority scheduling, and round robin. First-come first-served is simple but can produce poor average waiting time. Round robin assigns each process a fixed time quantum and cycles through ready tasks, which improves responsiveness in time-sharing systems. Starvation can occur when lower-priority tasks wait indefinitely.
- [S3] *db_transactions_concurrency*: Durability means that once a transaction is committed, its effects persist even after a crash. Concurrency control is needed because many users may access the same data at the same time. Problems that can appear without proper control include lost updates, dirty reads, and non-repeatable reads. A lost update occurs when one transaction overwrites the result of another. A dirty read happens when a transaction reads data written by another transaction that has not yet committed. A non-repeatable read occurs when the same query returns different results within a single transaction because another transaction modified the data in the meantime. Locking and multiversion concurrency control are two common approaches to handling concurrency.
- [S4] *os_processes_threads_scheduling*: A process is an executing program with its own memory space, resources, and execution state. A thread is a smaller unit of execution within a process. Threads of the same process share memory and resources, which makes communication between them faster but also introduces synchronization issues. Context switching between processes is generally more expensive than switching between threads because more state must be saved and restored.
- [S5] *os_process_vs_thread*: Because each process has its own memory space, communication between processes usually requires inter-process communication mechanisms such as pipes, sockets, or shared memory. Threads communicate more easily because they share memory. This makes threads more efficient for tasks that need frequent communication, but it also introduces risks such as race conditions and synchronization problems. Creating and switching between processes is generally more expensive than creating and switching between threads because processes require more operating system overhead. Multithreading is useful for applications that perform multiple tasks concurrently, such as a web server handling multiple client requests or a program performing background work while keeping the user interface responsive. A process can contain one thread or multiple threads.

**Answer:** The common CPU scheduling algorithms listed are first-come first-served, shortest job first, priority scheduling, and round robin [S1].

**Required points:**
- `algorithms`: First-come first-served, shortest job first, priority scheduling and round robin.

*Reference:* First-come first-served, shortest job first, priority scheduling and round robin.  
*Case notes:* All four are needed for the point.

## v3_021

**Q:** What is the difference between normalization in databases and normalization of features?

**Sources the model saw:**

- [S1] *ml_feature_engineering*: Features are the inputs used by a machine learning model. Feature engineering is the process of selecting, transforming, and creating useful features from raw data. Feature scaling is commonly used to place features on comparable ranges. Normalization rescales values to a specific range. Standardization transforms values so they have zero mean and unit variance. Good features often improve model performance more than increasing model complexity.
- [S2] *db_normalization_intro*: Normalization is the process of organizing data in a relational database to reduce redundancy and improve data integrity. Poorly designed tables often repeat the same facts in multiple rows, which can cause update anomalies, insertion anomalies, and deletion anomalies. An update anomaly happens when the same fact must be changed in several places and some copies are missed. An insertion anomaly happens when a new fact cannot be inserted without adding unrelated data.
- [S3] *ml_supervised_learning_basics*: Regression predicts continuous values, such as the price of a house. During training, the model minimizes a loss function that measures the difference between predictions and true labels. Training error refers to performance on the training set, while test error refers to performance on new unseen data. A model that performs very well on training data but poorly on test data is said to be overfitting. A model that performs poorly even on training data may be underfitting. Feature selection, regularization, and cross-validation are common techniques used to improve generalization.
- [S4] *db_normalization_intro*: Normalization is the process of organizing data in a relational database to reduce redundancy and improve data integrity. Poorly designed tables often repeat the same facts in multiple rows, which can cause update anomalies, insertion anomalies, and deletion anomalies. An update anomaly happens when the same fact must be changed in several places and some copies are missed. An insertion anomaly happens when a new fact cannot be inserted without adding unrelated data. A deletion anomaly happens when removing one row accidentally removes other valuable information. The first normal form requires that each attribute contain atomic values and that there are no repeating groups. The second normal form removes partial dependency, meaning that non-key attributes must depend on the whole primary key rather than just part of a composite key. The third normal form removes transitive dependency, so non-key attributes should not depend on other non-key attributes.
- [S5] *ml_overfitting_underfitting*: Underfitting occurs when a model is too simple to capture patterns in the training data. Underfit models typically have high bias and poor performance on both training and test data. Overfitting occurs when a model learns noise and specific details of the training data instead of general patterns. Overfit models often perform well on training data but poorly on unseen data. Model complexity influences the balance between underfitting and overfitting. Techniques such as regularization, cross-validation, and collecting more data can help reduce overfitting. The bias-variance tradeoff explains the relationship between model complexity and generalization performance.

**Answer:** Normalization in databases is the process of organizing data to reduce redundancy and improve data integrity, while normalization of features is a process used in machine learning to rescale values to a specific range. The former addresses issues like update, insertion, and deletion anomalies in relational databases [S2], [S4], whereas the latter focuses on preparing features for model training by ensuring they are on comparable scales [S1].

**Required points:**
- `database`: In databases, normalization organizes data to reduce redundancy and improve data integrity.
- `features`: For features, normalization rescales values to a specific range.

*Reference:* Database normalization organizes relational data to reduce redundancy and improve integrity; feature normalization rescales values to a specific range.  
*Case notes:* Ambiguous term across notes: retrieval must find both.

## v3_022

**Q:** What signs of overfitting do the notes describe?

**Sources the model saw:**

- [S1] *ml_overfitting_underfitting*: Underfitting occurs when a model is too simple to capture patterns in the training data. Underfit models typically have high bias and poor performance on both training and test data. Overfitting occurs when a model learns noise and specific details of the training data instead of general patterns. Overfit models often perform well on training data but poorly on unseen data. Model complexity influences the balance between underfitting and overfitting.
- [S2] *ml_overfitting_underfitting*: Underfitting occurs when a model is too simple to capture patterns in the training data. Underfit models typically have high bias and poor performance on both training and test data. Overfitting occurs when a model learns noise and specific details of the training data instead of general patterns. Overfit models often perform well on training data but poorly on unseen data. Model complexity influences the balance between underfitting and overfitting. Techniques such as regularization, cross-validation, and collecting more data can help reduce overfitting. The bias-variance tradeoff explains the relationship between model complexity and generalization performance.
- [S3] *ml_supervised_learning_basics*: Regression predicts continuous values, such as the price of a house. During training, the model minimizes a loss function that measures the difference between predictions and true labels. Training error refers to performance on the training set, while test error refers to performance on new unseen data. A model that performs very well on training data but poorly on test data is said to be overfitting. A model that performs poorly even on training data may be underfitting. Feature selection, regularization, and cross-validation are common techniques used to improve generalization.
- [S4] *ml_bias_variance_generalization*: Increasing model complexity can reduce bias but may increase variance. Regularization can reduce variance by discouraging overly complex models. Cross-validation is used to estimate how well a model is likely to perform on unseen data. In k-fold cross-validation, the dataset is divided into k subsets, and the model is trained multiple times, each time leaving out one subset for validation. A gap between training accuracy and validation accuracy is often a sign of overfitting. Selecting a model is not only about maximizing training performance but about achieving robust performance on unseen examples.
- [S5] *db_transactions_concurrency*: A transaction is a logical unit of work that must either complete entirely or have no effect at all. The ACID properties describe the reliability of transactions. Atomicity means all operations of a transaction happen or none happen. Consistency means the database moves from one valid state to another valid state. Isolation means concurrent transactions should not interfere in a way that produces incorrect results.

**Answer:** A gap between training accuracy and validation accuracy is often a sign of overfitting [S4].

**Required points:**
- `train_vs_unseen`: Performing well on training data but poorly on unseen or test data.
- `accuracy_gap`: A gap between training accuracy and validation accuracy is often a sign of overfitting.

*Reference:* Overfit models often perform well on training data but poorly on unseen data, and a gap between training and validation accuracy is often a sign of overfitting.  
*Case notes:* Preserve often.

## v3_023

**Q:** What role does cross-validation play in evaluating a model?

**Sources the model saw:**

- [S1] *ml_cross_validation*: Cross-validation evaluates model performance by repeatedly splitting data into training and validation sets. K-fold cross-validation divides data into k subsets. Each subset serves as the validation set once. Cross-validation reduces the risk of relying on a single train-test split. It is commonly used to estimate model generalization performance.
- [S2] *ml_bias_variance_generalization*: Increasing model complexity can reduce bias but may increase variance. Regularization can reduce variance by discouraging overly complex models. Cross-validation is used to estimate how well a model is likely to perform on unseen data. In k-fold cross-validation, the dataset is divided into k subsets, and the model is trained multiple times, each time leaving out one subset for validation. A gap between training accuracy and validation accuracy is often a sign of overfitting. Selecting a model is not only about maximizing training performance but about achieving robust performance on unseen examples.
- [S3] *ml_bias_variance_generalization*: The bias-variance tradeoff helps explain prediction error in machine learning models. Bias refers to error caused by overly simplistic assumptions in the learning algorithm. High-bias models are usually too simple and may underfit the training data. Variance refers to error caused by excessive sensitivity to the training data. High-variance models may fit noise in the training set and therefore overfit. Good generalization requires balancing these two sources of error. Increasing model complexity can reduce bias but may increase variance. Regularization can reduce variance by discouraging overly complex models. Cross-validation is used to estimate how well a model is likely to perform on unseen data. In k-fold cross-validation, the dataset is divided into k subsets, and the model is trained multiple times, each time leaving out one subset for validation. A gap between training accuracy and validation accuracy is often a sign of overfitting.
- [S4] *ml_model_evaluation*: Model evaluation measures how well a machine learning model performs on unseen data. A model should not only fit the training data but also generalize to new examples. A confusion matrix summarizes classification results using true positives, true negatives, false positives, and false negatives. Accuracy measures the proportion of correct predictions. Accuracy can be misleading on imbalanced datasets. Precision measures how many predicted positive instances are actually positive. Recall measures how many actual positive instances are correctly identified. The F1 score combines precision and recall into a single metric and is useful when both are important. Cross-validation is often used to obtain a more reliable estimate of model performance.
- [S5] *ml_supervised_learning_basics*: Regression predicts continuous values, such as the price of a house. During training, the model minimizes a loss function that measures the difference between predictions and true labels. Training error refers to performance on the training set, while test error refers to performance on new unseen data. A model that performs very well on training data but poorly on test data is said to be overfitting. A model that performs poorly even on training data may be underfitting. Feature selection, regularization, and cross-validation are common techniques used to improve generalization.

**Answer:** Cross-validation evaluates model performance by repeatedly splitting data into training and validation sets, reducing the risk of relying on a single train-test split. It is commonly used to estimate model generalization performance and provides a more reliable estimate of how well a model is likely to perform on unseen data [S1], [S4].

**Required points:**
- `estimate_unseen`: It estimates how well a model is likely to perform on unseen data (its generalization performance).
- `more_reliable`: It is often used to obtain a more reliable estimate of model performance.

*Reference:* It estimates how well a model is likely to perform on unseen data and is often used to obtain a more reliable estimate of model performance.  
*Case notes:* Evidence spread over three notes.

## v3_025

**Q:** Which three kinds of anomalies can poorly designed tables cause, and what is a deletion anomaly?

**Sources the model saw:**

- [S1] *db_normalization_intro*: A deletion anomaly happens when removing one row accidentally removes other valuable information. The first normal form requires that each attribute contain atomic values and that there are no repeating groups. The second normal form removes partial dependency, meaning that non-key attributes must depend on the whole primary key rather than just part of a composite key. The third normal form removes transitive dependency, so non-key attributes should not depend on other non-key attributes. For example, if a student table stores department_name and department_office, and department_office depends on department_name rather than student_id, then the design has a transitive dependency. Decomposition is often used to split such a table into smaller relations while preserving data meaning.
- [S2] *db_normalization_intro*: Normalization is the process of organizing data in a relational database to reduce redundancy and improve data integrity. Poorly designed tables often repeat the same facts in multiple rows, which can cause update anomalies, insertion anomalies, and deletion anomalies. An update anomaly happens when the same fact must be changed in several places and some copies are missed. An insertion anomaly happens when a new fact cannot be inserted without adding unrelated data.
- [S3] *db_normalization_intro*: Normalization is the process of organizing data in a relational database to reduce redundancy and improve data integrity. Poorly designed tables often repeat the same facts in multiple rows, which can cause update anomalies, insertion anomalies, and deletion anomalies. An update anomaly happens when the same fact must be changed in several places and some copies are missed. An insertion anomaly happens when a new fact cannot be inserted without adding unrelated data. A deletion anomaly happens when removing one row accidentally removes other valuable information. The first normal form requires that each attribute contain atomic values and that there are no repeating groups. The second normal form removes partial dependency, meaning that non-key attributes must depend on the whole primary key rather than just part of a composite key. The third normal form removes transitive dependency, so non-key attributes should not depend on other non-key attributes.
- [S4] *ml_supervised_learning_basics*: Regression predicts continuous values, such as the price of a house. During training, the model minimizes a loss function that measures the difference between predictions and true labels. Training error refers to performance on the training set, while test error refers to performance on new unseen data. A model that performs very well on training data but poorly on test data is said to be overfitting. A model that performs poorly even on training data may be underfitting. Feature selection, regularization, and cross-validation are common techniques used to improve generalization.
- [S5] *ml_overfitting_underfitting*: Underfitting occurs when a model is too simple to capture patterns in the training data. Underfit models typically have high bias and poor performance on both training and test data. Overfitting occurs when a model learns noise and specific details of the training data instead of general patterns. Overfit models often perform well on training data but poorly on unseen data. Model complexity influences the balance between underfitting and overfitting.

**Answer:** Poorly designed tables can cause update anomalies, insertion anomalies, and deletion anomalies [S2]. A deletion anomaly happens when removing one row accidentally removes other valuable information [S1].

**Required points:**
- `three_anomalies`: Update, insertion and deletion anomalies.
- `deletion`: A deletion anomaly happens when removing one row accidentally removes other valuable information.

*Reference:* Update, insertion and deletion anomalies. A deletion anomaly happens when removing one row accidentally removes other valuable information.  
*Case notes:* Both parts required.

## v3_026

**Q:** What is a transaction, and what does consistency mean in ACID?

**Sources the model saw:**

- [S1] *db_transactions_concurrency*: A transaction is a logical unit of work that must either complete entirely or have no effect at all. The ACID properties describe the reliability of transactions. Atomicity means all operations of a transaction happen or none happen. Consistency means the database moves from one valid state to another valid state. Isolation means concurrent transactions should not interfere in a way that produces incorrect results.
- [S2] *db_transactions_concurrency*: A transaction is a logical unit of work that must either complete entirely or have no effect at all. The ACID properties describe the reliability of transactions. Atomicity means all operations of a transaction happen or none happen. Consistency means the database moves from one valid state to another valid state. Isolation means concurrent transactions should not interfere in a way that produces incorrect results. Durability means that once a transaction is committed, its effects persist even after a crash. Concurrency control is needed because many users may access the same data at the same time. Problems that can appear without proper control include lost updates, dirty reads, and non-repeatable reads. A lost update occurs when one transaction overwrites the result of another. A dirty read happens when a transaction reads data written by another transaction that has not yet committed.
- [S3] *db_transactions_concurrency*: Durability means that once a transaction is committed, its effects persist even after a crash. Concurrency control is needed because many users may access the same data at the same time. Problems that can appear without proper control include lost updates, dirty reads, and non-repeatable reads. A lost update occurs when one transaction overwrites the result of another. A dirty read happens when a transaction reads data written by another transaction that has not yet committed. A non-repeatable read occurs when the same query returns different results within a single transaction because another transaction modified the data in the meantime. Locking and multiversion concurrency control are two common approaches to handling concurrency.
- [S4] *db_normalization_intro*: Normalization is the process of organizing data in a relational database to reduce redundancy and improve data integrity. Poorly designed tables often repeat the same facts in multiple rows, which can cause update anomalies, insertion anomalies, and deletion anomalies. An update anomaly happens when the same fact must be changed in several places and some copies are missed. An insertion anomaly happens when a new fact cannot be inserted without adding unrelated data. A deletion anomaly happens when removing one row accidentally removes other valuable information. The first normal form requires that each attribute contain atomic values and that there are no repeating groups. The second normal form removes partial dependency, meaning that non-key attributes must depend on the whole primary key rather than just part of a composite key. The third normal form removes transitive dependency, so non-key attributes should not depend on other non-key attributes.
- [S5] *ml_feature_engineering*: Features are the inputs used by a machine learning model. Feature engineering is the process of selecting, transforming, and creating useful features from raw data. Feature scaling is commonly used to place features on comparable ranges. Normalization rescales values to a specific range. Standardization transforms values so they have zero mean and unit variance. Good features often improve model performance more than increasing model complexity.

**Answer:** A transaction is a logical unit of work that must either complete entirely or have no effect at all [S1]. Consistency means the database moves from one valid state to another valid state [S1].

**Required points:**
- `transaction`: A transaction is a logical unit of work that must either complete entirely or have no effect at all.
- `consistency`: Consistency means the database moves from one valid state to another valid state.

*Reference:* A logical unit of work that either completes entirely or has no effect; consistency means the database moves from one valid state to another.  
*Case notes:* Both parts required.

## v3_027

**Q:** What is feature scaling for, and how do normalization and standardization differ?

**Sources the model saw:**

- [S1] *ml_feature_engineering*: Features are the inputs used by a machine learning model. Feature engineering is the process of selecting, transforming, and creating useful features from raw data. Feature scaling is commonly used to place features on comparable ranges. Normalization rescales values to a specific range. Standardization transforms values so they have zero mean and unit variance. Good features often improve model performance more than increasing model complexity.
- [S2] *db_normalization_intro*: Normalization is the process of organizing data in a relational database to reduce redundancy and improve data integrity. Poorly designed tables often repeat the same facts in multiple rows, which can cause update anomalies, insertion anomalies, and deletion anomalies. An update anomaly happens when the same fact must be changed in several places and some copies are missed. An insertion anomaly happens when a new fact cannot be inserted without adding unrelated data.
- [S3] *ml_supervised_learning_basics*: Regression predicts continuous values, such as the price of a house. During training, the model minimizes a loss function that measures the difference between predictions and true labels. Training error refers to performance on the training set, while test error refers to performance on new unseen data. A model that performs very well on training data but poorly on test data is said to be overfitting. A model that performs poorly even on training data may be underfitting. Feature selection, regularization, and cross-validation are common techniques used to improve generalization.
- [S4] *db_normalization_intro*: Normalization is the process of organizing data in a relational database to reduce redundancy and improve data integrity. Poorly designed tables often repeat the same facts in multiple rows, which can cause update anomalies, insertion anomalies, and deletion anomalies. An update anomaly happens when the same fact must be changed in several places and some copies are missed. An insertion anomaly happens when a new fact cannot be inserted without adding unrelated data. A deletion anomaly happens when removing one row accidentally removes other valuable information. The first normal form requires that each attribute contain atomic values and that there are no repeating groups. The second normal form removes partial dependency, meaning that non-key attributes must depend on the whole primary key rather than just part of a composite key. The third normal form removes transitive dependency, so non-key attributes should not depend on other non-key attributes.
- [S5] *ml_bias_variance_generalization*: Increasing model complexity can reduce bias but may increase variance. Regularization can reduce variance by discouraging overly complex models. Cross-validation is used to estimate how well a model is likely to perform on unseen data. In k-fold cross-validation, the dataset is divided into k subsets, and the model is trained multiple times, each time leaving out one subset for validation. A gap between training accuracy and validation accuracy is often a sign of overfitting. Selecting a model is not only about maximizing training performance but about achieving robust performance on unseen examples.

**Answer:** Feature scaling is commonly used to place features on comparable ranges [S1]. Normalization rescales values to a specific range, while standardization transforms values so they have zero mean and unit variance [S1].

**Required points:**
- `scaling`: Feature scaling places features on comparable ranges.
- `normalization`: Normalization rescales values to a specific range.
- `standardization`: Standardization transforms values to zero mean and unit variance.

*Reference:* Feature scaling places features on comparable ranges. Normalization rescales values to a specific range; standardization gives them zero mean and unit variance.  
*Case notes:* Three points. Must not mix in database normalization.

## v3_028

**Q:** What is the goal of supervised learning, and what does the model minimize during training?

**Sources the model saw:**

- [S1] *ml_supervised_learning_basics*: Supervised learning is a machine learning paradigm in which a model learns from labeled examples. Each training example contains input features and a target output. The goal is to learn a mapping from inputs to outputs so that the model can generalize to unseen data. Supervised learning tasks are often divided into classification and regression. Classification predicts discrete categories, such as whether an email is spam or not spam. Regression predicts continuous values, such as the price of a house. During training, the model minimizes a loss function that measures the difference between predictions and true labels. Training error refers to performance on the training set, while test error refers to performance on new unseen data. A model that performs very well on training data but poorly on test data is said to be overfitting. A model that performs poorly even on training data may be underfitting.
- [S2] *ml_supervised_learning_basics*: Supervised learning is a machine learning paradigm in which a model learns from labeled examples. Each training example contains input features and a target output. The goal is to learn a mapping from inputs to outputs so that the model can generalize to unseen data. Supervised learning tasks are often divided into classification and regression. Classification predicts discrete categories, such as whether an email is spam or not spam.
- [S3] *ml_supervised_learning_basics*: Regression predicts continuous values, such as the price of a house. During training, the model minimizes a loss function that measures the difference between predictions and true labels. Training error refers to performance on the training set, while test error refers to performance on new unseen data. A model that performs very well on training data but poorly on test data is said to be overfitting. A model that performs poorly even on training data may be underfitting. Feature selection, regularization, and cross-validation are common techniques used to improve generalization.
- [S4] *ml_gradient_descent*: Gradient descent is an optimization algorithm used to minimize a loss function. The algorithm updates model parameters in the direction that reduces prediction error. The learning rate controls the size of parameter updates. A learning rate that is too large may cause divergence. A learning rate that is too small may result in slow convergence. Gradient descent is a fundamental component of many machine learning algorithms and neural networks.
- [S5] *ml_bias_variance_generalization*: The bias-variance tradeoff helps explain prediction error in machine learning models. Bias refers to error caused by overly simplistic assumptions in the learning algorithm. High-bias models are usually too simple and may underfit the training data. Variance refers to error caused by excessive sensitivity to the training data. High-variance models may fit noise in the training set and therefore overfit. Good generalization requires balancing these two sources of error. Increasing model complexity can reduce bias but may increase variance. Regularization can reduce variance by discouraging overly complex models. Cross-validation is used to estimate how well a model is likely to perform on unseen data. In k-fold cross-validation, the dataset is divided into k subsets, and the model is trained multiple times, each time leaving out one subset for validation. A gap between training accuracy and validation accuracy is often a sign of overfitting.

**Answer:** The goal of supervised learning is to learn a mapping from inputs to outputs so that the model can generalize to unseen data. During training, the model minimizes a loss function that measures the difference between predictions and true labels [S1].

**Required points:**
- `goal`: To learn a mapping from inputs to outputs that generalizes to unseen data.
- `loss`: A loss function measuring the difference between predictions and true labels.

*Reference:* To learn a mapping from inputs to outputs that generalizes to unseen data; it minimizes a loss function measuring the difference between predictions and true labels.  
*Case notes:* Both parts required.

## v3_029

**Q:** What is multithreading useful for, and which two examples are given?

**Sources the model saw:**

- [S1] *os_process_vs_thread*: Creating and switching between processes is generally more expensive than creating and switching between threads because processes require more operating system overhead. Multithreading is useful for applications that perform multiple tasks concurrently, such as a web server handling multiple client requests or a program performing background work while keeping the user interface responsive. A process can contain one thread or multiple threads. If a process has only one thread, it is called single-threaded. If it has multiple threads, it is called multithreaded. In summary, a process provides isolation and resource ownership, while a thread provides a lightweight path of execution within a process.
- [S2] *os_process_vs_thread*: Because each process has its own memory space, communication between processes usually requires inter-process communication mechanisms such as pipes, sockets, or shared memory. Threads communicate more easily because they share memory. This makes threads more efficient for tasks that need frequent communication, but it also introduces risks such as race conditions and synchronization problems. Creating and switching between processes is generally more expensive than creating and switching between threads because processes require more operating system overhead. Multithreading is useful for applications that perform multiple tasks concurrently, such as a web server handling multiple client requests or a program performing background work while keeping the user interface responsive. A process can contain one thread or multiple threads.
- [S3] *os_processes_threads_scheduling*: A process is an executing program with its own memory space, resources, and execution state. A thread is a smaller unit of execution within a process. Threads of the same process share memory and resources, which makes communication between them faster but also introduces synchronization issues. Context switching between processes is generally more expensive than switching between threads because more state must be saved and restored. CPU scheduling determines which ready process or thread gets access to the processor. Common scheduling algorithms include first-come first-served, shortest job first, priority scheduling, and round robin. First-come first-served is simple but can produce poor average waiting time. Round robin assigns each process a fixed time quantum and cycles through ready tasks, which improves responsiveness in time-sharing systems. Starvation can occur when lower-priority tasks wait indefinitely.
- [S4] *ml_classification_regression*: Classification predicts discrete categories. Examples include spam detection, disease diagnosis, and sentiment analysis. Regression predicts continuous numerical values. Examples include house price prediction and temperature forecasting. Classification and regression are the two main categories of supervised learning problems. The choice between classification and regression depends on the type of target variable.
- [S5] *os_processes_threads_scheduling*: CPU scheduling determines which ready process or thread gets access to the processor. Common scheduling algorithms include first-come first-served, shortest job first, priority scheduling, and round robin. First-come first-served is simple but can produce poor average waiting time. Round robin assigns each process a fixed time quantum and cycles through ready tasks, which improves responsiveness in time-sharing systems. Starvation can occur when lower-priority tasks wait indefinitely. Aging is a technique used to gradually increase the priority of waiting tasks in order to reduce starvation. The distinction between process and thread is important for performance, isolation, and system design.

**Answer:** Multithreading is useful for applications that perform multiple tasks concurrently, such as a web server handling multiple client requests or a program performing background work while keeping the user interface responsive [S1].

**Required points:**
- `concurrent_tasks`: Applications that perform multiple tasks concurrently.
- `examples`: A web server handling multiple client requests, and a program doing background work while keeping the user interface responsive.

*Reference:* Applications that perform multiple tasks concurrently, such as a web server handling many client requests or a program doing background work while keeping its interface responsive.  
*Case notes:* Both examples are needed for the examples point.

## v3_030

**Q:** What is the difference between training error and test error?

**Sources the model saw:**

- [S1] *ml_supervised_learning_basics*: Regression predicts continuous values, such as the price of a house. During training, the model minimizes a loss function that measures the difference between predictions and true labels. Training error refers to performance on the training set, while test error refers to performance on new unseen data. A model that performs very well on training data but poorly on test data is said to be overfitting. A model that performs poorly even on training data may be underfitting. Feature selection, regularization, and cross-validation are common techniques used to improve generalization.
- [S2] *ml_supervised_learning_basics*: Supervised learning is a machine learning paradigm in which a model learns from labeled examples. Each training example contains input features and a target output. The goal is to learn a mapping from inputs to outputs so that the model can generalize to unseen data. Supervised learning tasks are often divided into classification and regression. Classification predicts discrete categories, such as whether an email is spam or not spam. Regression predicts continuous values, such as the price of a house. During training, the model minimizes a loss function that measures the difference between predictions and true labels. Training error refers to performance on the training set, while test error refers to performance on new unseen data. A model that performs very well on training data but poorly on test data is said to be overfitting. A model that performs poorly even on training data may be underfitting.
- [S3] *ml_bias_variance_generalization*: The bias-variance tradeoff helps explain prediction error in machine learning models. Bias refers to error caused by overly simplistic assumptions in the learning algorithm. High-bias models are usually too simple and may underfit the training data. Variance refers to error caused by excessive sensitivity to the training data. High-variance models may fit noise in the training set and therefore overfit. Good generalization requires balancing these two sources of error.
- [S4] *ml_bias_variance_generalization*: The bias-variance tradeoff helps explain prediction error in machine learning models. Bias refers to error caused by overly simplistic assumptions in the learning algorithm. High-bias models are usually too simple and may underfit the training data. Variance refers to error caused by excessive sensitivity to the training data. High-variance models may fit noise in the training set and therefore overfit. Good generalization requires balancing these two sources of error. Increasing model complexity can reduce bias but may increase variance. Regularization can reduce variance by discouraging overly complex models. Cross-validation is used to estimate how well a model is likely to perform on unseen data. In k-fold cross-validation, the dataset is divided into k subsets, and the model is trained multiple times, each time leaving out one subset for validation. A gap between training accuracy and validation accuracy is often a sign of overfitting.
- [S5] *ml_overfitting_underfitting*: Underfitting occurs when a model is too simple to capture patterns in the training data. Underfit models typically have high bias and poor performance on both training and test data. Overfitting occurs when a model learns noise and specific details of the training data instead of general patterns. Overfit models often perform well on training data but poorly on unseen data. Model complexity influences the balance between underfitting and overfitting.

**Answer:** Training error refers to performance on the training set, while test error refers to performance on new unseen data [S1].

**Required points:**
- `training_error`: Training error refers to performance on the training set.
- `test_error`: Test error refers to performance on new unseen data.

*Reference:* Training error is performance on the training set; test error is performance on new, unseen data.  
*Case notes:* Both parts required.

## v3_032

**Q:** Do good features always improve a model more than making it more complex?

**Sources the model saw:**

- [S1] *ml_feature_engineering*: Features are the inputs used by a machine learning model. Feature engineering is the process of selecting, transforming, and creating useful features from raw data. Feature scaling is commonly used to place features on comparable ranges. Normalization rescales values to a specific range. Standardization transforms values so they have zero mean and unit variance. Good features often improve model performance more than increasing model complexity.
- [S2] *ml_bias_variance_generalization*: Increasing model complexity can reduce bias but may increase variance. Regularization can reduce variance by discouraging overly complex models. Cross-validation is used to estimate how well a model is likely to perform on unseen data. In k-fold cross-validation, the dataset is divided into k subsets, and the model is trained multiple times, each time leaving out one subset for validation. A gap between training accuracy and validation accuracy is often a sign of overfitting. Selecting a model is not only about maximizing training performance but about achieving robust performance on unseen examples.
- [S3] *ml_bias_variance_generalization*: The bias-variance tradeoff helps explain prediction error in machine learning models. Bias refers to error caused by overly simplistic assumptions in the learning algorithm. High-bias models are usually too simple and may underfit the training data. Variance refers to error caused by excessive sensitivity to the training data. High-variance models may fit noise in the training set and therefore overfit. Good generalization requires balancing these two sources of error. Increasing model complexity can reduce bias but may increase variance. Regularization can reduce variance by discouraging overly complex models. Cross-validation is used to estimate how well a model is likely to perform on unseen data. In k-fold cross-validation, the dataset is divided into k subsets, and the model is trained multiple times, each time leaving out one subset for validation. A gap between training accuracy and validation accuracy is often a sign of overfitting.
- [S4] *ml_overfitting_underfitting*: Underfitting occurs when a model is too simple to capture patterns in the training data. Underfit models typically have high bias and poor performance on both training and test data. Overfitting occurs when a model learns noise and specific details of the training data instead of general patterns. Overfit models often perform well on training data but poorly on unseen data. Model complexity influences the balance between underfitting and overfitting. Techniques such as regularization, cross-validation, and collecting more data can help reduce overfitting. The bias-variance tradeoff explains the relationship between model complexity and generalization performance.
- [S5] *ml_supervised_learning_basics*: Regression predicts continuous values, such as the price of a house. During training, the model minimizes a loss function that measures the difference between predictions and true labels. Training error refers to performance on the training set, while test error refers to performance on new unseen data. A model that performs very well on training data but poorly on test data is said to be overfitting. A model that performs poorly even on training data may be underfitting. Feature selection, regularization, and cross-validation are common techniques used to improve generalization.

**Answer:** Good features often improve model performance more than increasing model complexity [S1].

**Required points:**
- `often`: Not always: good features often improve performance more than increasing model complexity.

*Reference:* The notes say good features often, not always, improve performance more than increasing model complexity.  
*Case notes:* Preserve often (C4).

## v3_033

**Q:** Are high-bias models always too simple?

**Sources the model saw:**

- [S1] *ml_bias_variance_generalization*: The bias-variance tradeoff helps explain prediction error in machine learning models. Bias refers to error caused by overly simplistic assumptions in the learning algorithm. High-bias models are usually too simple and may underfit the training data. Variance refers to error caused by excessive sensitivity to the training data. High-variance models may fit noise in the training set and therefore overfit. Good generalization requires balancing these two sources of error.
- [S2] *ml_overfitting_underfitting*: Underfitting occurs when a model is too simple to capture patterns in the training data. Underfit models typically have high bias and poor performance on both training and test data. Overfitting occurs when a model learns noise and specific details of the training data instead of general patterns. Overfit models often perform well on training data but poorly on unseen data. Model complexity influences the balance between underfitting and overfitting. Techniques such as regularization, cross-validation, and collecting more data can help reduce overfitting. The bias-variance tradeoff explains the relationship between model complexity and generalization performance.
- [S3] *ml_overfitting_underfitting*: Underfitting occurs when a model is too simple to capture patterns in the training data. Underfit models typically have high bias and poor performance on both training and test data. Overfitting occurs when a model learns noise and specific details of the training data instead of general patterns. Overfit models often perform well on training data but poorly on unseen data. Model complexity influences the balance between underfitting and overfitting.
- [S4] *ml_bias_variance_generalization*: The bias-variance tradeoff helps explain prediction error in machine learning models. Bias refers to error caused by overly simplistic assumptions in the learning algorithm. High-bias models are usually too simple and may underfit the training data. Variance refers to error caused by excessive sensitivity to the training data. High-variance models may fit noise in the training set and therefore overfit. Good generalization requires balancing these two sources of error. Increasing model complexity can reduce bias but may increase variance. Regularization can reduce variance by discouraging overly complex models. Cross-validation is used to estimate how well a model is likely to perform on unseen data. In k-fold cross-validation, the dataset is divided into k subsets, and the model is trained multiple times, each time leaving out one subset for validation. A gap between training accuracy and validation accuracy is often a sign of overfitting.
- [S5] *ml_bias_variance_generalization*: Increasing model complexity can reduce bias but may increase variance. Regularization can reduce variance by discouraging overly complex models. Cross-validation is used to estimate how well a model is likely to perform on unseen data. In k-fold cross-validation, the dataset is divided into k subsets, and the model is trained multiple times, each time leaving out one subset for validation. A gap between training accuracy and validation accuracy is often a sign of overfitting. Selecting a model is not only about maximizing training performance but about achieving robust performance on unseen examples.

**Answer:** High-bias models are usually too simple [S1].

**Required points:**
- `usually`: Not always: high-bias models are usually too simple and may underfit.

*Reference:* The notes say high-bias models are usually too simple and may underfit, not always.  
*Case notes:* Preserve usually and may (C4).
