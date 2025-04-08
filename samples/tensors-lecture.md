# Tensor Methods in Machine Learning

## MATH-5510: Advanced Topics in Linear Algebra

### Dr. Julian Bennett, Week 8, Lecture 1

*[Professor Bennett enters the lecture hall wearing his characteristic tweed jacket with leather elbow patches over a light blue oxford shirt. His salt-and-pepper hair is slightly disheveled, and his round spectacles sit low on his nose. He carries a worn leather messenger bag from which he retrieves chalk, notes, and a vacuum flask of tea. He adjusts the sleeves of his jacket as he surveys the room.]*

Good morning, everyone! I trust you've had a productive week grappling with the spectral decomposition problems I set. Today, we're venturing into territory that extends beyond the matrices we've become comfortable with over the past two months. We're going to explore tensors—mathematical objects that generalize vectors and matrices to higher dimensions.

*[He pours steaming tea into the cap of his flask and takes a quick sip before setting it down.]*

Tensors have become increasingly important in machine learning, data analysis, and scientific computing. While the mathematical formalism can be daunting at first glance, I assure you that the core ideas are natural extensions of concepts you're already familiar with.

*[He moves to the blackboard and begins writing in a precise, measured hand.]*

## From Vectors to Matrices to Tensors: The Dimensional Hierarchy

Let's begin by placing tensors in their proper context within the hierarchy of mathematical objects we've studied.

A scalar is a single number—a zero-dimensional object, if you will.

A vector is a one-dimensional array of numbers. We can index its elements with a single subscript: v_i.

A matrix is a two-dimensional array, indexed with two subscripts: A_ij.

*[He gestures with chalk in hand, his British accent becoming more pronounced as his enthusiasm grows.]*

A tensor, then, extends this pattern to higher dimensions. A third-order tensor would be a three-dimensional array, indexed with three subscripts: T_ijk. We can continue to fourth-order tensors and beyond, each time adding another dimension and another index.

*[He draws a diagram showing the progression from point to line to square to cube.]*

This dimensional hierarchy gives us a powerful way to represent increasingly complex data structures and relationships. While our visual intuition begins to fail us beyond three dimensions, the mathematical framework remains perfectly coherent.

*[He takes another sip of tea.]*

One point of clarification: In physics and engineering, "tensor" has a specific meaning related to coordinate transformations. In data science and machine learning, we typically use the term more loosely to refer to multidimensional arrays. For our purposes today, I'll adopt the latter convention.

## Tensor Operations and Notation

Before we dive into applications, let's establish some fundamental operations and notation for working with tensors.

*[He wipes a portion of the board clean and begins writing again.]*

We'll denote tensors with bold capital letters: **T**, **X**, **Y**. The order of a tensor—sometimes called its rank, though this can be confused with matrix rank—refers to the number of dimensions or modes.

Indexing follows naturally from matrices: T_ijk refers to the element at position (i,j,k) in a third-order tensor **T**.

*[He pauses, pushing his spectacles back up his nose.]*

Fibers are the higher-dimensional analogue of matrix rows and columns. In a third-order tensor, we have three types of fibers:

- Mode-1 fibers: T_i:: (fixing j and k)
- Mode-2 fibers: T_:j: (fixing i and k)
- Mode-3 fibers: T_::k (fixing i and j)

*[He gestures to indicate the different directions.]*

Slices are two-dimensional sections of a tensor, obtained by fixing all but two indices. For a third-order tensor, we might have horizontal, lateral, or frontal slices.

*[He draws an example of a cube with different slices highlighted.]*

Now, the fundamental operation in tensor algebra is the tensor product, which generalizes the outer product of vectors. If **a** is a vector of length I and **b** is a vector of length J, their tensor product **a** ⊗ **b** is a matrix of size I × J with elements (a ⊗ b)_ij = a_i × b_j.

This extends naturally to higher orders. The tensor product of three vectors **a**, **b**, and **c** gives a third-order tensor with elements (a ⊗ b ⊗ c)_ijk = a_i × b_j × c_k.

*[He steps back from the board, looking thoughtfully at his notation.]*

Another crucial operation is tensor contraction, which reduces the order of a tensor by summing over paired indices. The most familiar example is matrix multiplication, which can be viewed as contracting the columns of one matrix with the rows of another.

*[He writes the Einstein summation notation on the board.]*

C_ik = sum_j A_ij B_jk

This generalizes to higher-order tensors in straightforward ways, though the notation can become unwieldy. Einstein summation convention, which implicitly sums over repeated indices, is particularly useful in these contexts.

*[He takes another sip of tea.]*

## Tensor Decompositions: Factorizing Higher-Order Data

Now, let's turn to the heart of today's lecture: tensor decompositions. These are higher-dimensional analogues of matrix factorizations like the singular value decomposition we studied earlier.

*[He begins drawing diagrams of different tensor decompositions.]*

The fundamental question is this: How can we express a complex tensor in terms of simpler components? For matrices, the answer includes factorizations like SVD, which expresses a matrix as a sum of rank-one matrices. Similar principles apply to tensors, but with some fascinating new wrinkles.

Let's start with the simplest tensor decomposition: the CP decomposition, where CP stands for CANDECOMP/PARAFAC, names reflecting its independent discovery by different researchers.

*[He writes the decomposition formula.]*

For a third-order tensor **T**, the CP decomposition expresses it as a sum of R component rank-one tensors:

T_ijk ≈ sum from r=1 to R of a_ir × b_jr × c_kr

Here, **a_r**, **b_r**, and **c_r** are vectors that capture patterns along each mode of the tensor.

*[He gestures enthusiastically.]*

What's remarkable about the CP decomposition is that it's essentially unique under mild conditions, unlike matrix factorizations which have rotational ambiguity. This uniqueness is a powerful property that makes CP decomposition particularly useful for feature extraction and latent factor discovery.

*[He moves to a different part of the board.]*

Another important decomposition is the Tucker decomposition, which can be viewed as a higher-order generalization of principal component analysis. It expresses a tensor as:

T_ijk ≈ sum from p=1 to P, sum from q=1 to Q, sum from r=1 to R of g_pqr × a_ip × b_jq × c_kr

Here, **G** is a smaller "core tensor" that captures the interactions between components, while the matrices **A**, **B**, and **C** represent the principal components along each mode.

*[He pauses, noticing some confused looks.]*

I realize these expressions may seem abstract at first. Let me give you a concrete example to ground our understanding.

## Tensors in Action: A Computer Vision Example

*[He retrieves a small stack of printed images from his bag.]*

Consider the problem of facial recognition. Each grayscale image can be represented as a matrix, with elements corresponding to pixel intensities. If we collect images of different people under different lighting conditions and viewing angles, we naturally obtain a third-order tensor: people × lighting × angles.

*[He holds up some of the images to illustrate.]*

Using CP decomposition, we might discover that this tensor can be approximated by a sum of rank-one components, each representing a particular facial feature under varying conditions. The vectors **a_r** would capture features across individuals, **b_r** would capture how these features appear under different lighting, and **c_r** would capture how they transform under different viewing angles.

*[His eyes light up as he explains.]*

This decomposition achieves something remarkable: it separates intrinsic facial characteristics from lighting and viewpoint effects. This is precisely the kind of disentanglement that's valuable in computer vision and other machine learning tasks.

*[He takes another sip of tea.]*

The Tucker decomposition offers even more flexibility by allowing interactions between these components through the core tensor. It might reveal, for instance, that certain facial features are more affected by specific lighting conditions or viewpoints than others.

*[He returns to the board.]*

## Computational Challenges and Algorithms

Now, let's briefly discuss the computational aspects of tensor methods. Unlike matrices, many tensor problems are NP-hard in the worst case. This includes determining the exact rank of a tensor—the minimum number of rank-one components needed for an exact CP decomposition.

*[He speaks with a slight frown.]*

This computational complexity has led to the development of various approximation algorithms. For CP decomposition, the workhorse is Alternating Least Squares (ALS), which fixes all but one set of factors, solves for the optimal values of those factors, then cycles through all factor sets until convergence.

*[He writes the outline of the ALS algorithm.]*

Initialize factors **A**, **B**, **C**
Repeat until convergence:

  1. Fix **B** and **C**, solve for **A**
  2. Fix **A** and **C**, solve for **B**
  3. Fix **A** and **B**, solve for **C**

Each of these subproblems reduces to a linear least squares problem, which we can solve efficiently.

*[He gestures to indicate iteration.]*

Similar approaches work for Tucker decomposition, though the presence of the core tensor adds complexity. Various optimization techniques like gradient descent, stochastic methods, and more specialized approaches like Higher-Order SVD (HOSVD) or Higher-Order Orthogonal Iteration (HOOI) have been developed to handle these challenges.

*[He pauses, looking at his watch.]*

I see we're approaching the halfway mark of our lecture. Let's take a brief three-minute break to stretch and absorb what we've covered so far. When we return, we'll explore tensor methods in machine learning applications.

*[Professor Bennett sips his tea and chats with a few students who approach with questions during the break. After three minutes, he clears his throat to resume.]*

## Tensors in Machine Learning: From Theory to Practice

Welcome back. Now that we've established the mathematical foundations, let's explore how tensor methods are applied in contemporary machine learning.

*[He moves to a clear section of the board.]*

One major application is in dimensionality reduction and feature extraction. Just as principal component analysis uses the dominant eigenvectors of a data covariance matrix, multilinear PCA and other tensor-based methods can extract features from multidimensional data while preserving structural relationships.

*[He draws a diagram of images projected into a lower-dimensional space.]*

In natural language processing, word embeddings can be organized into matrices, with rows corresponding to words and columns to feature dimensions. If we want to represent relationships between words across multiple contexts or languages, tensors provide a natural representation.

*[He gestures animatedly.]*

For instance, a third-order tensor might represent word-context-language relationships, with a CP decomposition revealing cross-lingual semantic patterns. This has applications in machine translation and multilingual text analysis.

*[He takes another sip of tea.]*

In recommendation systems, the classic matrix completion problem involves predicting missing entries in a user-item matrix. With tensors, we can incorporate additional dimensions such as time, context, or item features. A third-order tensor might represent user-item-time interactions, allowing the system to capture evolving preferences.

*[He draws a cube representing this tensor.]*

These applications highlight a general principle: tensors are valuable whenever data has natural multidimensional structure that we wish to preserve. Flattening a tensor into a matrix or vector often destroys important relationships between dimensions.

## The Curse and Blessing of Dimensionality in Tensor Methods

*[He adopts a more serious tone.]*

As we move to higher-dimensional tensors, we encounter both challenges and opportunities related to the curse of dimensionality.

*[He writes "n^d" on the board and underlines it for emphasis.]*

An order-d tensor with n elements along each dimension contains n^d entries total. This exponential growth makes storing and processing high-order tensors prohibitively expensive for large n and d.

*[He raises a finger in caution.]*

However, tensor decompositions can be remarkably efficient for high-dimensional data. A CP decomposition with R components requires only O(ndR) parameters to approximate an order-d tensor, compared to the O(n^d) elements in the full tensor. When d is large, this compression can be substantial.

*[He gestures with growing enthusiasm.]*

This is sometimes called the "blessing of dimensionality"—the fact that structured high-dimensional data often lies on or near a low-dimensional manifold that can be efficiently captured by tensor methods.

*[He walks back to the center of the board.]*

Another fascinating aspect is that certain problems become easier in higher dimensions. In matrix completion, we need structural assumptions like low-rank or sparsity to recover missing entries. But in tensor completion, uniqueness properties of tensor decompositions sometimes allow recovery with fewer observations, under certain conditions.

*[He pushes his spectacles back up his nose.]*

This hints at a deeper mathematical truth: tensors have algebraic properties that are qualitatively different from matrices, not merely quantitatively different. The transition from matrices to tensors isn't just about adding more indices—it's about entering a new mathematical landscape with its own unique features.

## Tensor Networks and Quantum Machine Learning

Before we wrap up, I want to touch on a cutting-edge area where tensor methods are making significant impacts: quantum computing and quantum machine learning.

*[He draws a simple diagram of connected tensors.]*

Tensor networks are structured arrangements of tensors connected by contractions along specific dimensions. They've long been used in quantum physics to efficiently represent quantum many-body states that would otherwise require exponentially large matrices.

*[His chalk moves quickly as he sketches various tensor network architectures.]*

These include Matrix Product States (MPS), Projected Entangled Pair States (PEPS), and the Multi-scale Entanglement Renormalization Ansatz (MERA). Each provides a different trade-off between expressiveness and computational efficiency.

*[He speaks with genuine excitement.]*

What's particularly fascinating is how these quantum-inspired tensor methods are now feeding back into classical machine learning. Various tensor network architectures are being used to parameterize neural networks, especially for problems with sequential or hierarchical structure.

*[He gestures to indicate this cross-disciplinary flow.]*

For instance, MPS-inspired models have shown promise for sequence modeling tasks traditionally handled by recurrent neural networks. The mathematical connections between quantum entanglement and statistical correlations in data provide a rich theoretical foundation for these approaches.

*[He takes a final sip of tea, emptying his flask.]*

This cross-pollination between physics, mathematics, and machine learning exemplifies why tensor methods are so fascinating. They sit at the intersection of multiple disciplines, providing both practical tools and theoretical insights.

## Conclusion and Future Directions

*[He begins gathering his notes.]*

We've covered significant ground today, from the basic definition of tensors to advanced decompositions and applications in machine learning. I hope you've gained an appreciation for how tensors extend our familiar linear algebraic tools to handle multilinear relationships in complex data.

As we conclude, let me highlight a few active research directions that you might find interesting for further exploration:

*[He counts off on his fingers.]*

First, tensor methods for non-linear dimensionality reduction, where the goal is to capture manifold structure in high-dimensional data without assuming linearity.

Second, robust tensor decompositions that can handle corrupted or missing data, which are crucial for real-world applications.

Third, distributed and parallel algorithms for tensor computations, enabling tensor methods to scale to truly massive datasets.

Fourth, specialized hardware accelerators for tensor operations, including quantum computing approaches for certain classes of tensor problems.

*[He closes his notebook with a decisive motion.]*

For next week, please read Chapter 8 of the textbook, focusing on sections 8.3 through 8.7 on applications of tensor methods in machine learning. The problem set, which I'll post this afternoon, will include both theoretical exercises on tensor decompositions and a practical component implementing CP decomposition for a simple image dataset.

*[He looks up at the class, a slight smile playing at the corners of his mouth.]*

Remember that while the mathematics may initially seem abstract, tensors provide a natural language for describing complex, multi-faceted data. As you work through the exercises, try to maintain both the formal rigor of the mathematics and an intuitive understanding of what these operations mean for the data.

Are there any questions before we conclude?

*[A student asks about the relationship between tensor decompositions and neural networks.]*

Ah, excellent question! The relationship between tensor decompositions and neural networks runs deeper than many realize. Consider a fully connected layer in a neural network with a nonlinearity. It computes something like f(Wx + b), where W is a weight matrix, x is the input vector, b is a bias term, and f is a nonlinear activation function.

If we stack multiple such layers, each with its own weight matrix, we're essentially performing a sequence of matrix-vector products followed by nonlinearities. Now, what's interesting is that if we were to "unfold" certain tensor decompositions like CP or Tucker, we'd get structures remarkably similar to neural network layers.

*[He sketches quickly on the board.]*

For instance, a CP decomposition can be viewed as a single-hidden-layer network with linear activation, where the hidden layer size corresponds to the rank of the decomposition. Tucker decomposition similarly relates to neural networks with specific architectural constraints.

Some researchers have exploited this connection to design neural network architectures that incorporate tensor decompositions explicitly, either as initialization strategies or as structural components. This can lead to more parameter-efficient models, especially for problems with natural tensor structure.

The field of tensor networks goes even further, proposing entirely new neural architectures inspired by quantum physics models. These approaches are particularly promising for data with complex hierarchical or sequential correlations.

*[He nods at another student.]*

Regarding your question about implementation frameworks—yes, there are several excellent libraries for tensor computations. In Python, TensorLy provides a unified interface for tensor methods that works with various deep learning backends like PyTorch and TensorFlow. For MATLAB users, the Tensor Toolbox from Sandia National Labs is quite comprehensive.

For large-scale applications, frameworks like TensorFlow and PyTorch offer substantial support for tensor operations, though they're primarily geared toward neural networks rather than classical tensor decompositions. More specialized libraries exist for particular applications or decomposition types.

One practical tip: start with small tensors where you can verify results manually before scaling up to larger problems. Tensor algorithms can sometimes be sensitive to initialization and optimization parameters, so building intuition on toy examples is valuable.

*[He glances at his watch.]*

I see we're out of time. Thank you for your excellent questions and attention today. Don't hesitate to email me or visit during office hours if you'd like to discuss any of these topics further. Tensor methods are a particular passion of mine, and I'm always happy to explore them in more depth with interested students.

*[Professor Bennett carefully packs his empty flask and chalk into his leather messenger bag, adjusts his tweed jacket, and exits the lecture hall with a thoughtful expression, already mentally sketching problems for next week's assignment.]*
