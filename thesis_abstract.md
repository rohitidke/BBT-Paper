# Working Title

Unsupervised Contextual Bundling for Capturing Intra-Categorical Structure in Large Object-Attribute Matrices

# Motivation and Problem Statement

Concepts are often represented with binary object-attribute matrices, where rows correspond to exemplars and columns to attributes. A central problem is that large matrices usually contain many irrelevant or weakly informative attributes. These attributes distort the induced conceptual structure and make it difficult to identify bundles that meaningfully represent category-internal organization. In contextual bundling, this problem is addressed by constructing a simplified model matrix and comparing it to the original matrix. The fit between both matrices can then be interpreted as an indicator of how typical an exemplar is within its category.

The central challenge of this thesis is therefore not only to apply contextual bundling, but to make it work in an unsupervised way for capturing intra-categorical structure. This means constructing model matrices without manual intervention, identifying meaningful bundles, selecting preferred bundle structures, and evaluating whether the resulting representation reflects graded category structure in a psychologically plausible way.

# Research Questions

1. How can contextual bundling be formulated as an unsupervised method for capturing intra-categorical structure in large object-attribute matrices?
2. How can meaningful and preferred bundles be identified from the induced model matrix without relying on manual supervision?
3. To what extent does model-matrix quality affect the recovery of graded intra-categorical structure as reflected by human typicality ratings?
4. How do different attribute spaces, especially category-level versus exemplar-level and filtered versus unfiltered matrices, influence the success of unsupervised contextual bundling?

# Data and Methodology

The thesis is based on the Leuven Conceptual Data, which provides human-generated object-attribute matrices and typicality ratings for the domains Animals and Artifacts. The analysis considers both category-level and exemplar-level attributes. In addition, filtered exemplar matrices are used to study the role of attribute relevance, including frequency-based filtering, importance-based filtering, and random attribute selection as a control condition.

Methodologically, the thesis studies how model matrices can be constructed for contextual bundling in an unsupervised and scalable way. Boolean Matrix Decomposition is used as a conceptual and methodological baseline. In addition, an image-processing-based Boolean Matrix Factorization pipeline is used as a practical unsupervised approach for handling larger matrices. In this pipeline, reordered binary matrices are treated as images and bundles are extracted from rectangular patterns after banded-structure induction. In the current project, this pipeline is implemented with Barycenter-based ordering and OTSU-based bundle detection, and evaluated across multiple parameter settings.

The evaluation combines structural and behavioral criteria. Structural quality is measured through matrix-wide Jaccard goodness of fit, bundle purity, and distinct category-label matching. Behavioral validity is measured by computing object-level fit values and correlating them with human typicality ratings for each category. This makes it possible to distinguish between a model that reconstructs the matrix well and a model that also captures psychologically plausible graded category structure.

# Expected Contribution

The thesis is expected to make three contributions. First, it will provide a clearer methodological account of unsupervised contextual bundling as a way to capture intra-categorical structure. Second, it will clarify the role of model-matrix quality for identifying preferred bundles and for interpreting graded category structure. Third, it will assess whether more concrete exemplar-level attributes, especially after relevance-based filtering, improve the recovery of intra-categorical structure beyond what is possible with abstract category-level attributes.

Current results suggest that contextual bundling works most reliably when the model matrix fits the data well, with the clearest positive results appearing for Animals at category level. Exemplar-level settings are more challenging, but the broader project infrastructure now supports systematic run-wise comparison, preferred-run selection, and extended evaluation across filtered attribute spaces.

# Abstract

This master's thesis investigates how intra-categorical structure can be captured from large binary object-attribute matrices using unsupervised contextual bundling. The central assumption is that concepts are not represented by rigid necessary-and-sufficient features, but by graded internal structure in which some exemplars are more typical than others. Contextual bundling addresses this by constructing a simplified model matrix from the original incidence matrix and interpreting the correspondence between both matrices as an indicator of exemplar typicality. In large and sparse matrices, however, irrelevant attributes can distort this process, making the unsupervised construction of a well-fitting model matrix the key challenge.

The thesis focuses on contextual bundling as the main methodological object of study. Using the Leuven Conceptual Data for Animals and Artifacts, I compare category-level and exemplar-level object-attribute matrices, as well as filtered exemplar matrices based on feature frequency, feature importance, and random selection. The goal is to study how meaningful bundles can be induced without supervision, how preferred bundles can be selected from the resulting model matrices, and under which conditions these bundles capture graded intra-categorical structure.

Methodologically, the thesis uses Boolean Matrix Decomposition as a baseline and studies scalable unsupervised alternatives based on image-processing-driven Boolean Matrix Factorization. The evaluation combines matrix reconstruction quality with psychological validity. Model quality is assessed using Jaccard goodness of fit, bundle purity, and distinct category-label mapping quality, while behavioral validity is evaluated by correlating object-level fit values with human typicality ratings. The thesis therefore examines not only whether a model matrix approximates the original data, but also whether it captures the graded category structure perceived by human participants.

The expected outcome is a clearer account of when unsupervised contextual bundling can recover intra-categorical structure and how this depends on model-matrix quality, parameterization, and attribute selection strategy. In particular, the thesis aims to show that scalable unsupervised model-matrix construction is essential for selecting preferred bundles and for making contextual bundling usable on larger exemplar-level datasets.

# What We Have Done and Why We Have Done It

- We reproduced earlier contextual bundling results at category level.
  - Why:
    - establish a reliable baseline
    - verify that our implementation is consistent with established findings

- We analyzed both Animals and Artifacts domains from the Leuven Conceptual Data.
  - Why:
    - check whether the observed structure is robust across domains
    - avoid drawing conclusions from only one type of concept

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

- We used Boolean Matrix Decomposition as a classical baseline.
  - Why:
    - it is the standard contextual bundling approach in earlier literature
    - it gives us a clear reference point for unsupervised contextual bundling

- We implemented and evaluated an image-processing-based Boolean Matrix Factorization pipeline.
  - Why:
    - Boolean Matrix Decomposition does not scale well to larger exemplar-level matrices
    - an efficient unsupervised alternative is needed

- We explored multiple parameter settings and selected preferred runs.
  - Why:
    - no single configuration is best under every criterion
    - systematic comparison is needed to identify preferred bundles and useful model matrices

- We evaluated model matrices with Jaccard goodness of fit, bundle purity, and category-label matching.
  - Why:
    - a good bundle solution should look structurally reasonable
    - it should also reconstruct the original matrix in a meaningful way

- We correlated object-level fit values with human typicality ratings.
  - Why:
    - this is the key test of psychological validity
    - it shows whether the derived bundles reflect graded category structure

- We observed that good behavioral interpretation depends strongly on good model-matrix fit.
  - Why:
    - without a well-fitting model matrix, bundle selection becomes less reliable
    - correlations with human judgments become harder to interpret

- We found that the clearest positive results appear at category level, especially for Animals, while exemplar-level settings remain more challenging.
  - Why:
    - category-level results are currently more stable and interpretable
    - exemplar-level settings remain methodologically challenging
    - this motivates the thesis focus on unsupervised contextual bundling and better model-matrix construction
