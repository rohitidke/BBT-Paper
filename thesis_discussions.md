# Title

Unsupervised model matrix post-processing for Detecting Intra-Categorical Structure for Large Binary Objects-Attributes Matrices

Comments:
Focus on Large matrices 
but
UCB can be applied to small matrix as well

small matrices -> contextual bundling by ceuleman and storms

Mention and Explain (in Introduction) 2008 feature applicability rating, ceulemans and storms :
What is Intra-Categorical Structuring and why? difference to inter-categorical structuring

Major paper for foundations:  
1988 de boeck rosenberg (HICLAS).
storms 1994 (why HICLAS concept representation is feasible wrt intra inter structuring), 
ceulemans and storms 2010 (HICLAS is able to reflect intra structure on large binary matrices), 
Use recent paper (Contextual bundling -> model matrix and fit measure)
HICLAS is edge case, where it reflects intra structure for binary small matrix

matrin trencka
leuven concept data

TODO: *Unsupervised model matrix construction or Unsupervised Contextual Bundling???* 

Contextual bundling?
1. model matrix construction
2. model fit measure (production ready model matrix vs orginal matrix)


model matrix construction:
- permuting orginal matrix (reordering)
- Adding rectangles or bundles (BMD, BMF, human judgement)
  - bundles or rectangles
  - Raw model matrix
- post-processing model matrix***** (Main Focus)
  - production ready model matrix by:
    - all bundles
    - preferred bundles

FOR bmd, we already have production ready model matrix, but not for others


# Abstract:

- Intra-categorical structuring
  - Intra-categorical structuring refers to the internal structure within a specific semantic category
  - It captures the "graded structure" of categories, which acknowledges that not all members are equally good or representative examples of a category

- contextual bundling
  - Contextual bundling is a method used to detect and describe the intra-categorical structure of concepts by treating them as imperfect representations of the world
  - The process works by analyzing a binary object-attribute data matrix—mathematically referred to as a "formal context"—and identifying rectangular patterns of co-occurring objects and attributes. These identified patterns form simplified groupings known as "bundles".

  - Mechanically, contextual bundling involves the following steps:
    - Generating a model matrix: A simplified binary model matrix is created to capture the structural regularities and clusterings (bundles) of the original raw data.
    - Applying a fit measure: The method compares the original data matrix with the generated model matrix using a goodness-of-fit measure, most commonly the Jaccard index. 
    - Determining typicality: The degree of correspondence between the model matrix and the original matrix at the object level within these clusters is what is referred to as a "contextual bundle". This fit value serves as a quantitative score indicating how typical an exemplar is for a concept

- model matrix construction
  - model matrix construction for large binary object attribute matrices
  - raw model matrix is not production ready and why

  - Model matrix construction is the process of generating a simplified mathematical representation of an original binary object-attribute data matrix (often called a "formal context") to capture its underlying structural regularities
  - The goal of this construction is to approximate the original data by minimizing a loss function (the discrepancies between the original data and the model), subject to the restriction that the resulting model matrix consists of possibly overlapping rectangular blocks of 1s, representing "bundles",. Mathematically, it is constructed through Boolean decomposition, meaning the model matrix is the Boolean product of an object bundle matrix and an attribute bundle matrix
  - How it is done for large binary matrices: Traditionally, model matrices are constructed using Boolean Matrix Decomposition (BMD) algorithms, such as alternating least squares or simulated annealing,. However, these traditional methods are highly inefficient and cannot scale to very large object-attribute matrices
  - To solve this scaling problem, researchers have adapted an image processing pipeline for Boolean Matrix Factorization, which is significantly more efficient and can be applied to matrices of any size
  - But this raw model matrix generated is not good for detecting intra-categorical structure because there are multiple bundles for a category
- model matrix post-processing**
  - Therefore model matrix post-processing have been introduced to make raw model matrix good for detecting intra-categorical structure.
  - why it is important to process it in unsupervised manner?
    - Because we don't have the ground truth always available, i.e. which objects belongs to which category. 
    - selecting a preferred bundles should not be biased or it might not be able to capture the underline structure
- Approach:
  - Therefore our approcah is to select the preferred bundles based on highest avg attribute weight.
  - Once we get our preferred bundles, we can generate the final model matrix that is good for downstream tasks
- Evaluation:
  - We can evaluate model matrix using goodness of fit index to the original matrix
  - Similarly we can do it object wise.
  - Then we can do correlation analysis with human typicality rating to check whether it is able to capture semantic categorical strucutre or not
- Discussion:
  - Ceuleman did but on small matrices, not scalalble
  - New approcah can be applied to large as well small matrices
  - Any method could be used to detect the bundles


TODO:
1. write down abstract 43 to 49 lines
2. complete document for registration
  - Approach (Unsupervised postprocessing)
    - multiple bundles for category
    - preferred bundling
  - evaluation 
    - fit measure of model matrix
    - category wise fit
    - correlation analysis
  - Discussion
    - consideration of other papers 
    - related papers -> martin ,ceulemans have done
    - not done, so our constribution -> production ready model matrix

Sections of One pager for registration:
- Abstract
- References
  - leuven concept data

# Motivation and Problem Statement

...

# Research Questions

1. How can contextual bundling be formulated as an unsupervised method for capturing intra-categorical structure in large object-attribute matrices?
2. How can meaningful and preferred bundles be identified from the induced model matrix without relying on manual supervision?
3. To what extent does model-matrix quality affect the recovery of graded intra-categorical structure as reflected by human typicality ratings?
4. How do different attribute spaces, especially category-level versus exemplar-level and filtered versus unfiltered matrices, influence the success of unsupervised contextual bundling?

# Data and Methodology

The thesis is based on the Leuven Conceptual Data, which provides human-generated object-attribute matrices and typicality ratings for the domains Animals and Artifacts. The analysis considers both category-level and exemplar-level attributes. 

Methodologically, the thesis studies how model matrices can be constructed for contextual bundling in an unsupervised and scalable way. Boolean Matrix Decomposition is used as a conceptual and methodological baseline. In addition, an image-processing-based Boolean Matrix Factorization pipeline is used as a practical unsupervised approach for handling larger matrices.

The evaluation combines structural and behavioral criteria. Structural quality is measured through matrix-wide Jaccard goodness of fit, bundle purity, and distinct category-label matching. Behavioral validity is measured by computing object-level fit values and correlating them with human typicality ratings for each category. This makes it possible to distinguish between a model that reconstructs the matrix well and a model that also captures psychologically plausible graded category structure.

# Expected Contribution

The thesis is expected to make three contributions. 
- First, it will provide a clearer methodological account of unsupervised contextual bundling as a way to capture intra-categorical structure. 
- Second, it will clarify the role of model-matrix quality for identifying preferred bundles and for interpreting graded category structure. 
- Third, it will assess whether more concrete exemplar-level attributes, (especially after relevance-based filtering**), improve the recovery of intra-categorical structure beyond what is possible with abstract category-level attributes.


# Abstract

This master's thesis investigates how intra-categorical structure can be captured from large binary object-attribute matrices using unsupervised contextual bundling. The central assumption is that categories are not represented by rigid features, but by graded internal structure in which some exemplars are more typical than others. Contextual bundling addresses this by constructing a simplified model matrix from the original incidence matrix and interpreting the correspondence between both matrices as an indicator of exemplar typicality. In large and sparse matrices, however, irrelevant attributes can distort this process, making the unsupervised construction of a well-fitting model matrix the key challenge.

The thesis focuses on contextual bundling as the main methodological object of study. The goal is to study how meaningful bundles can be induced without supervision, how preferred bundles can be selected from the resulting model matrices, and under which conditions these bundles capture graded intra-categorical structure.

Methodologically, the thesis uses Boolean Matrix Decomposition as a baseline and studies scalable unsupervised alternatives based on image-processing-driven Boolean Matrix Factorization. The evaluation combines matrix reconstruction quality with psychological validity. Model quality is assessed using Jaccard goodness of fit, bundle purity, and distinct category-label mapping quality, while behavioral validity is evaluated by correlating object-level fit values with human typicality ratings. The thesis therefore examines not only whether a model matrix approximates the original data, but also whether it captures the graded category structure perceived by human participants.

The expected outcome is a clearer account of when unsupervised contextual bundling can recover intra-categorical structure and how this depends on model-matrix quality, parameterization, and attribute selection strategy. In particular, the thesis aims to show that scalable unsupervised model-matrix construction is essential for selecting preferred bundles and for making contextual bundling usable on larger exemplar-level datasets.






# Implementation

## Project goal

To study whether **unsupervised contextual bundling** can recover
meaningful internal structure inside concept categories such as animals and artifacts.

In simple terms, we start from large binary object-attribute matrices and ask:

- can we automatically group similar patterns into bundles?
- can we build a simplified **model matrix** that still represents the original data well?
- does the fit between data and model reflect **human typicality ratings**?


## What We Have Done and Why We Have Done It

- We reproduced the Ceulemans & Storms contextual bundling results at category level.
  - Why:
    - establish a reliable baseline
    - verify that our implementation is consistent with established findings
	
- Collect and organize the Leuven Conceptual Data
	- Why:
		- to test the method on more than one semantic domain
		- to compare abstract category-level features with more concrete exemplar-level features

- Used image processing methods
	- Why:
		- Performance is fast
		- works for bigger matrices as well unlike BMD
		- supports unsupervised way of bundling
		
- Built model matrix
	- why:
		- Original matrix too noisy and contain irrelevant data
		- capture the main bundles or patterns in the matrix


- Visualize the model matrix
	- why:
		- check whether the bundles are clear and meaningful

 - Computed overall model fit with original matrix 
    - Why:
      - To observe whether good behavioral interpretation depends strongly on good model-matrix fit
      - without a well-fitting model matrix, bundle selection becomes less reliable

- Correlation analysis with human typicality ratings
	- why:
		- to test:
			- whether the structure found by the model is psychologically meaningful
			- does the model capture graded category structure?
		

- We explored multiple parameter settings and selected preferred runs.
  - Why:
    - no single configuration is best under every criterion
    - systematic comparison is needed to identify preferred bundles and useful model matrices

- We compared category-level matrices with exemplar-level matrices.
  - Why:
    - category-level attributes are more abstract
    - exemplar-level attributes are more concrete
    - compare which representation captures intra-categorical structure better

- We studied filtered exemplar matrices based on feature frequency, feature importance, and random selection.
  - Why:
    - test whether reducing irrelevant attributes improves bundle quality
    - test whether filtering improves model fit
    - test whether filtering improves correlation with human typicality ratings