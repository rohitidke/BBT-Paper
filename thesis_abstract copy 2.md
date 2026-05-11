# Working Title

Unsupervised Contextual Bundling for Detecting Intra-Categorical Structure in Large Object-Attribute Matrices

# Motivation and Problem Statement

Concepts are often represented with binary object-attribute matrices, where rows correspond to exemplars and columns to attributes. A central problem is that large matrices usually contain many irrelevant or weakly informative attributes. These attributes distort the induced conceptual structure and make it difficult to identify bundles that meaningfully represent category-internal organization. In contextual bundling, this problem is addressed by constructing a simplified model matrix and comparing it to the original matrix. The fit between both matrices can then be interpreted as an indicator of how typical an exemplar is within its category.

Our published paper showed that contextual bundling can reproduce earlier findings on graded category structure and that this idea remains meaningful when moving from classical Boolean matrix decomposition to a more scalable image-processing-based Boolean matrix factorization pipeline. At the same time, the results also showed an important limitation: good behavioral interpretation depends strongly on the quality of the constructed model matrix. This makes the unsupervised construction of a good model matrix the core methodological challenge.

The planned master's thesis takes this challenge as its main focus. Rather than treating contextual bundling only as a descriptive technique, the thesis studies how model matrices can be generated in an unsupervised and scalable way, how preferred bundles can be selected, and under which conditions the resulting structure aligns with human typicality judgments.

# Research Questions

1. How can a model matrix for contextual bundling be constructed in an unsupervised and scalable way for large object-attribute matrices?
2. To what extent does better model-matrix fit lead to a better approximation of intra-categorical structure as reflected by human typicality ratings?
3. How do category-level versus exemplar-level attributes, as well as filtered versus unfiltered attribute sets, affect bundle quality, model fit, and typicality correlation?

# Data and Methodology

The thesis is based on the Leuven Conceptual Data, which provides human-generated object-attribute matrices and typicality ratings for the domains Animals and Artifacts. The analysis considers both category-level attributes and exemplar-level attributes. In addition, filtered exemplar matrices are used to study the role of attribute relevance, including frequency-based filtering, importance-based filtering, and random attribute selection as a control condition.

Methodologically, the thesis compares two ways of constructing model matrices. The first is Boolean Matrix Decomposition (BMD), which serves as the classical baseline and reproduces earlier contextual bundling results. The second is an image-processing-based Boolean Matrix Factorization (BMF) pipeline, in which reordered binary matrices are treated as images and bundles are extracted from rectangular patterns after banded-structure induction. In the current project, this pipeline is implemented with Barycenter-based ordering and OTSU-based bundle detection, and evaluated across multiple parameter settings.

The evaluation combines structural and behavioral criteria. Structural quality is measured through matrix-wide Jaccard goodness of fit between the original matrix and the reconstructed model matrix, together with bundle purity and distinct category-label matching. Behavioral validity is measured by computing object-level fit values and correlating them with human typicality ratings for each category. This makes it possible to distinguish between a model that reconstructs the matrix well and a model that also captures psychologically plausible graded category structure.

# Expected Contribution

The thesis is expected to make three contributions. First, it will provide a systematic comparison between classical BMD and a scalable image-processing BMF approach for contextual bundling. Second, it will clarify the role of model-matrix quality for selecting preferred bundles and for interpreting intra-categorical structure. Third, it will offer an empirical assessment of whether more concrete exemplar-level attributes, especially after relevance-based filtering, can improve the recovery of graded category structure beyond what is possible with abstract category-level attributes.

Preliminary results from the published paper and the project experiments suggest that contextual bundling works most reliably when the model matrix fits the data well, with the clearest positive results appearing for Animals at category level. Exemplar-level settings are more challenging, but the broader project infrastructure now supports systematic run-wise comparison, preferred-run selection, and extended evaluation across filtered attribute spaces. The thesis will consolidate these results, refine the evaluation, and derive a clearer methodological account of when unsupervised contextual bundling can serve as a meaningful model of intra-categorical concept structure.

# Abstract

This master's thesis investigates how intra-categorical structure can be detected from large binary object-attribute matrices using contextual bundling. The central assumption is that concepts are not represented by rigid necessary-and-sufficient features, but by graded internal structure in which some exemplars are more typical than others. Contextual bundling addresses this by constructing a simplified model matrix from the original incidence matrix and interpreting the correspondence between both matrices as an indicator of exemplar typicality. However, in large and sparse matrices, irrelevant attributes can distort this process, making the unsupervised construction of a well-fitting model matrix the key challenge.

The thesis builds on our published paper on contextual bundling and extends it into a broader methodological study. Using the Leuven Conceptual Data for Animals and Artifacts, I compare category-level and exemplar-level object-attribute matrices, as well as filtered exemplar matrices based on feature frequency, feature importance, and random selection. The methodological core is a comparison between classical Boolean Matrix Decomposition and a scalable image-processing-based Boolean Matrix Factorization pipeline for generating model matrices and contextual bundles.

The evaluation combines matrix reconstruction quality with psychological validity. Model quality is assessed using Jaccard goodness of fit, bundle purity, and distinct category-label mapping quality. To evaluate whether the derived structure is behaviorally meaningful, object-level fit values are correlated with human typicality ratings. The thesis therefore examines not only whether a model matrix approximates the original data, but also whether it captures the graded category structure perceived by human participants.

The expected outcome is a clearer account of when contextual bundling can recover intra-categorical structure and how this depends on the choice of modeling method, parameterization, and attribute selection strategy. In particular, the thesis aims to show that scalable unsupervised model-matrix construction is essential for selecting preferred bundles and for making contextual bundling usable on larger exemplar-level datasets. By combining formal analysis, empirical evaluation, and implementation-based comparison, the thesis contributes to a better understanding of how category-internal conceptual structure can be modeled from high-dimensional binary data.
