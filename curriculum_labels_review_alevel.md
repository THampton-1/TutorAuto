# A-Level curriculum labels & sub-skills — review

**What this is.** A proposed short `label` and `sub-skills` breakdown for the Edexcel A Level
Mathematics (9MA0) spec points, produced with the same technique as the GCSE review doc
(`curriculum_labels_review.md`). You review and hand-edit; I load your final version.
**Status:** Pure (62 nodes) reviewed and signed off by Theo 2026-10-10. Statistics and
Mechanics (27 nodes) added below for review (ADR-015).

**The technique (unchanged from GCSE):**
1. Strip the objective verb, keep the mathematical object — the label is a noun phrase.
2. Collapse enumerations and bundles to the umbrella heading a teacher files it under.
3. Coordinate siblings so labels disambiguate *within a module* (decided module by module).
4. Use the canonical UK classroom name, verified — never an ad-hoc paraphrase.
5. Sub-skills = distinct teaching sessions. Usually the spec's own clauses; for a long
   enumeration, group the list into teaching units, don't split it item by item.
6. Atomic nodes keep a single sub-skill.
7. *(New for A-Level.)* A topic that is only in the spec's Guidance column but is normally a
   lesson of its own (parametric areas, coding, inclined planes, ladders) gets its own
   sub-skill, flagged in a Grain check as Guidance-sourced — otherwise it has no home.

**New for A-Level — AS markers.** The spec prints AS content in bold, so each heading says
whether the point is *(AS)* (all of it), *(AS part)* (some of it) or neither (A-Level only, i.e.
typically Year 2). Where a point is only partly AS, I split sub-skills along that boundary and an
`AS:` line says which ones are AS — useful for Year 12 students like Francis. The `AS:` line and
the markers are for your information only; they are not loaded.

**How to edit.** Change any `Label:` or sub-skill line freely. Delete a sub-skill to merge, add
one to split. `⚠ Grain check` marks nodes where I think the breakdown is debatable — look
hardest at those. Don't touch the `### P…` headings or the `Spec:` lines (verbatim spec text and
the key I load against). Sub-skill IDs are assigned by position (P7.3 → P7.3.1, P7.3.2, …), so
reordering renumbers them — fine now, while nothing has been extracted against them.

**Spec text typed from page images.** 16 points have maths the PDF draws rather than stores
as text (fractions, √2, integrals); their `Spec:` text was typed from the rendered page and is
marked *(typed)*. Worth a glance: P1.1, P2.7, P4.1, P4.2, P5.1–5.3, P5.5, P6.3, P6.4, P7.2,
P8.2, P9.1, P9.3. One oddity kept as printed: P6.3 says x ⩾ 0 where x > 0 is meant.

---

## P1 — Proof

### P1.1  *(AS part)*
- **Label:** Proof
- **AS:** sub-skills 1–3 (contradiction is Year 2)
- **Sub-skills:**
  - Proof by deduction
  - Proof by exhaustion
  - Disproof by counter-example
  - Proof by contradiction (incl. √2 irrational, infinitely many primes)
- **Spec:** *(typed)* Understand and use the structure of mathematical proof, proceeding from given assumptions through a series of logical steps to a conclusion; use methods of proof, including: Proof by deduction; Proof by exhaustion; Disproof by counter example; Proof by contradiction (including proof of the irrationality of √2 and the infinity of primes, and application to unfamiliar proofs).

---

## P2 — Algebra and functions

### P2.1  *(AS)*
- **Label:** Indices
- **Sub-skills:**
  - Laws of indices (incl. negative & fractional)
- **Spec:** Understand and use the laws of indices for all rational exponents.

### P2.2  *(AS)*
- **Label:** Surds
- **Sub-skills:**
  - Simplifying & manipulating surds
  - Rationalising the denominator
- **Spec:** Use and manipulate surds, including rationalising the denominator.

### P2.3  *(AS)*
- **Label:** Quadratics
- **⚠ Grain check:** 5 sub-skills. Merge 'Solving' into 'Completing the square' if you never teach solving on its own at A-Level; keep 'Hidden quadratics' separate, as it's a distinct exam trick.
- **Sub-skills:**
  - Quadratic graphs
  - The discriminant (real, repeated & no roots)
  - Completing the square
  - Solving quadratic equations
  - Hidden quadratics (quadratic in a function of x)
- **Spec:** Work with quadratic functions and their graphs. The discriminant of a quadratic function, including the conditions for real and repeated roots. Completing the square. Solution of quadratic equations including solving quadratic equations in a function of the unknown.

### P2.4  *(AS)*
- **Label:** Simultaneous equations
- **Sub-skills:**
  - Linear simultaneous equations
  - One linear & one quadratic
- **Spec:** Solve simultaneous equations in two variables by elimination and by substitution, including one linear and one quadratic equation.

### P2.5  *(AS)*
- **Label:** Inequalities
- **⚠ Grain check:** 4 sub-skills; set notation is how answers are written rather than a lesson of its own, so merge it into the first two if you prefer.
- **Sub-skills:**
  - Linear inequalities
  - Quadratic inequalities
  - Set notation & 'and' / 'or' in answers
  - Inequalities on graphs (regions & shading)
- **Spec:** Solve linear and quadratic inequalities in a single variable and interpret such inequalities graphically, including inequalities with brackets and fractions. Express solutions through correct use of ‘and’ and ‘or’, or through set notation. Represent linear and quadratic inequalities such as y > x + 1 and y > ax² + bx + c graphically.

### P2.6  *(AS part)*
- **Label:** Polynomials & algebraic fractions
- **AS:** sub-skills 1–3 (algebraic fractions are Year 2)
- **Sub-skills:**
  - Expanding & factorising polynomials (incl. cubics)
  - Algebraic division
  - The factor theorem
  - Simplifying algebraic fractions
- **Spec:** Manipulate polynomials algebraically, including expanding brackets and collecting like terms, factorisation and simple algebraic division; use of the factor theorem. Simplify rational expressions, including by factorising and cancelling, and algebraic division (by linear expressions only).

### P2.7  *(AS part)*
- **Label:** Graphs of functions
- **AS:** all except modulus graphs
- **⚠ Grain check:** 5 sub-skills — the busiest algebra node. Intersections are often taught inside sketching; merge if so.
- **Sub-skills:**
  - Sketching polynomial graphs (cubics & quartics)
  - Modulus graphs (linear functions)
  - Reciprocal graphs y = a/x, y = a/x² & asymptotes
  - Solving equations using intersections
  - Proportional relationships & their graphs
- **Spec:** *(typed)* Understand and use graphs of functions; sketch curves defined by simple equations including polynomials. The modulus of a linear function. y = a/x and y = a/x² (including their vertical and horizontal asymptotes). Interpret algebraic solution of equations graphically; use intersection points of graphs to solve equations. Understand and use proportional relationships and their graphs.

### P2.8
- **Label:** Composite & inverse functions
- **Sub-skills:**
  - Composite functions
  - Inverse functions & their graphs
- **Spec:** Understand and use composite functions; inverse functions and their graphs.

### P2.9  *(AS part)*
- **Label:** Graph transformations
- **AS:** sub-skill 1 (combinations are Year 2)
- **Sub-skills:**
  - Single transformations: af(x), f(x) + a, f(x + a), f(ax)
  - Combined transformations
- **Spec:** Understand the effect of simple transformations on the graph of y = f(x), including sketching associated graphs: y = af(x), y = f(x) + a, y = f(x + a), y = f(ax) and combinations of these transformations

### P2.10
- **Label:** Partial fractions
- **⚠ Grain check:** Split by denominator type; merge if you teach both in one go.
- **Sub-skills:**
  - Partial fractions (distinct linear factors)
  - Partial fractions with a repeated linear factor
- **Spec:** Decompose rational functions into partial fractions (denominators not more complicated than squared linear terms and with no more than 3 terms, numerators constant or linear).

### P2.11
- **Label:** Modelling with functions
- **Sub-skills:**
  - Modelling with functions (limitations & refinements)
- **Spec:** Use of functions in modelling, including consideration of limitations and refinements of the models.

---

## P3 — Coordinate geometry in the (x, y) plane

### P3.1  *(AS)*
- **Label:** Straight-line graphs
- **Sub-skills:**
  - Equation of a straight line (y − y₁ = m(x − x₁), ax + by + c = 0)
  - Parallel & perpendicular lines
  - Straight-line models
- **Spec:** Understand and use the equation of a straight line, including the forms y – y₁ = m(x – x₁) and ax + by + c = 0; Gradient conditions for two straight lines to be parallel or perpendicular. Be able to use straight line models in a variety of contexts.

### P3.2  *(AS)*
- **Label:** Circles
- **Sub-skills:**
  - Equation of a circle
  - Completing the square to find centre & radius
  - Circle properties (semicircle, chord bisector, tangent ⟂ radius)
- **Spec:** Understand and use the coordinate geometry of the circle including using the equation of a circle in the form (x – a)² + (y – b)² = r² Completing the square to find the centre and radius of a circle; use of the following properties: ● the angle in a semicircle is a right angle ● the perpendicular from the centre to a chord bisects the chord ● the radius of a circle at a given point on its circumference is perpendicular to the tangent to the circle at that point.

### P3.3
- **Label:** Parametric equations
- **Sub-skills:**
  - Parametric equations of curves
  - Converting parametric ↔ Cartesian
- **Spec:** Understand and use the parametric equations of curves and conversion between Cartesian and parametric forms.

### P3.4
- **Label:** Parametric modelling
- **Sub-skills:**
  - Parametric equations in modelling
- **Spec:** Use parametric equations in modelling in a variety of contexts.

---

## P4 — Sequences and series

### P4.1  *(AS part)*
- **Label:** Binomial expansion
- **AS:** sub-skill 1 (rational n is Year 2)
- **Sub-skills:**
  - Binomial expansion for positive integer n (n!, ⁿCᵣ)
  - Binomial expansion for rational n (approximation & validity)
- **Spec:** *(typed)* Understand and use the binomial expansion of (a + bx)ⁿ for positive integer n; the notations n! and ⁿCᵣ link to binomial probabilities. Extend to any rational n, including its use for approximation; be aware that the expansion is valid for |bx/a| < 1 (proof not required).

### P4.2
- **Label:** Sequences
- **Sub-skills:**
  - Sequences from an nth-term formula
  - Recurrence relations xₙ₊₁ = f(xₙ)
  - Increasing, decreasing & periodic sequences
- **Spec:** *(typed)* Work with sequences including those given by a formula for the nth term and those generated by a simple relation of the form xₙ₊₁ = f(xₙ); increasing sequences; decreasing sequences; periodic sequences.

### P4.3
- **Label:** Sigma notation
- **Sub-skills:**
  - Sigma notation
- **Spec:** Understand and use sigma notation for sums of series.

### P4.4
- **Label:** Arithmetic sequences & series
- **⚠ Grain check:** Merge if nth term and sum are always one lesson for you.
- **Sub-skills:**
  - Arithmetic sequences (nth term)
  - Arithmetic series (sum to n terms)
- **Spec:** Understand and work with arithmetic sequences and series, including the formulae for nth term and the sum to n terms

### P4.5
- **Label:** Geometric sequences & series
- **Sub-skills:**
  - Geometric sequences (nth term)
  - Sum of a finite geometric series
  - Sum to infinity & convergence (|r| < 1)
- **Spec:** Understand and work with geometric sequences and series, including the formulae for the nth term and the sum of a finite geometric series; the sum to infinity of a convergent geometric series, including the use of |r| < 1; modulus notation

### P4.6
- **Label:** Modelling with sequences & series
- **Sub-skills:**
  - Sequences & series in modelling
- **Spec:** Use sequences and series in modelling.

---

## P5 — Trigonometry

### P5.1  *(AS part)*
- **Label:** Trig ratios, sine & cosine rules, radians
- **AS:** sub-skills 1–3 (radians are Year 2)
- **⚠ Grain check:** Merge the area rule into sine & cosine rules if they're one lesson.
- **Sub-skills:**
  - sin, cos & tan for any angle (unit circle)
  - Sine & cosine rules
  - Area of a triangle (½ab sin C)
  - Radians, arc length & sector area
- **Spec:** *(typed)* Understand and use the definitions of sine, cosine and tangent for all arguments; the sine and cosine rules; the area of a triangle in the form ½ab sin C. Work with radian measure, including use for arc length and area of sector.

### P5.2
- **Label:** Small angle approximations
- **Sub-skills:**
  - Small angle approximations
- **Spec:** *(typed)* Understand and use the standard small angle approximations of sine, cosine and tangent: sin θ ≈ θ, cos θ ≈ 1 − θ²/2, tan θ ≈ θ, where θ is in radians.

### P5.3  *(AS part)*
- **Label:** Trig graphs & exact values
- **AS:** sub-skill 1 (exact values in radians are Year 2)
- **Sub-skills:**
  - Graphs of sin, cos & tan (symmetry & periodicity)
  - Exact trig values (incl. radians)
- **Spec:** *(typed)* Understand and use the sine, cosine and tangent functions; their graphs, symmetries and periodicity. Know and use exact values of sin and cos for 0, π/6, π/4, π/3, π/2, π and multiples thereof, and exact values of tan for 0, π/6, π/4, π/3, π and multiples thereof.

### P5.4
- **Label:** Reciprocal & inverse trig functions
- **Sub-skills:**
  - sec, cosec & cot (definitions & graphs)
  - arcsin, arccos & arctan (graphs, domains & ranges)
- **Spec:** Understand and use the definitions of secant, cosecant and cotangent and of arcsin, arccos and arctan; their relationships to sine, cosine and tangent; understanding of their graphs; their ranges and domains.

### P5.5  *(AS part)*
- **Label:** Trig identities
- **AS:** sub-skill 1 (the sec/cosec identities are Year 2)
- **Sub-skills:**
  - tan θ = sin θ / cos θ and sin²θ + cos²θ = 1
  - sec²θ = 1 + tan²θ and cosec²θ = 1 + cot²θ
- **Spec:** *(typed)* Understand and use tan θ = sin θ / cos θ. Understand and use sin²θ + cos²θ = 1; sec²θ = 1 + tan²θ and cosec²θ = 1 + cot²θ.

### P5.6
- **Label:** Addition & double angle formulae
- **Sub-skills:**
  - Addition formulae sin, cos & tan (A ± B) (incl. geometric proof)
  - Double angle formulae
  - Harmonic form: a cos θ + b sin θ = R cos(θ ± α)
- **Spec:** Understand and use double angle formulae; use of formulae for sin (A ± B), cos (A ± B), and tan (A ± B), understand geometrical proofs of these formulae. Understand and use expressions for a cosθ+ bsinθ in the equivalent forms of rcos (θ±α) or rsin (θ±α)

### P5.7  *(AS)*
- **Label:** Solving trig equations
- **⚠ Grain check:** 3 sub-skills; merge the last two if you teach them together.
- **Sub-skills:**
  - Solving trig equations in an interval
  - Quadratic trig equations
  - Trig equations with multiple angles (e.g. sin 2x)
- **Spec:** Solve simple trigonometric equations in a given interval, including quadratic equations in sin, cos and tan and equations involving multiples of the unknown angle.

### P5.8
- **Label:** Trig proofs
- **Sub-skills:**
  - Proving trig identities
- **Spec:** Construct proofs involving trigonometric functions and identities.

### P5.9
- **Label:** Trigonometry in context
- **Sub-skills:**
  - Trigonometry in context (vectors, kinematics, forces)
- **Spec:** Use trigonometric functions to solve problems in context, including problems involving vectors, kinematics and forces.

---

## P6 — Exponentials and logarithms

### P6.1  *(AS)*
- **Label:** Exponential functions
- **Sub-skills:**
  - Exponential graphs (aˣ and eˣ)
- **Spec:** Know and use the function aˣ and its graph, where a is positive. Know and use the function eˣ and its graph.

### P6.2  *(AS)*
- **Label:** Gradient of eᵏˣ
- **Sub-skills:**
  - Gradient of eᵏˣ & exponential models
- **Spec:** Know that the gradient of eᵏˣ is equal to keᵏˣ and hence understand why the exponential model is suitable in many applications.

### P6.3  *(AS)*
- **Label:** Logarithms & ln x
- **Sub-skills:**
  - Definition of logₐ x (inverse of aˣ)
  - ln x & its graph (inverse of eˣ)
- **Spec:** *(typed)* Know and use the definition of logₐ x as the inverse of aˣ, where a is positive and x ⩾ 0. Know and use the function ln x and its graph. Know and use ln x as the inverse function of eˣ.

### P6.4  *(AS part)*
- **Label:** Laws of logarithms
- **Sub-skills:**
  - Laws of logarithms
- **Spec:** *(typed)* Understand and use the laws of logarithms: logₐ x + logₐ y = logₐ (xy); logₐ x − logₐ y = logₐ (x/y); k logₐ x = logₐ xᵏ (including, for example, k = −1 and k = −½).

### P6.5  *(AS)*
- **Label:** Exponential equations
- **Sub-skills:**
  - Solving aˣ = b
- **Spec:** Solve equations of the form aˣ =b

### P6.6  *(AS)*
- **Label:** Logarithmic graphs
- **⚠ Grain check:** Usually one lesson; merge if so.
- **Sub-skills:**
  - Linearising y = axⁿ (log y against log x)
  - Linearising y = kbˣ (log y against x)
- **Spec:** Use logarithmic graphs to estimate parameters in relationships of the form y = axⁿ and y = kbˣ, given data for x and y

### P6.7  *(AS)*
- **Label:** Exponential growth & decay
- **Sub-skills:**
  - Exponential growth & decay models
- **Spec:** Understand and use exponential growth and decay; use in modelling (examples may include the use of e in continuous compound interest, radioactive decay, drug concentration decay, exponential growth as a model for population growth); consideration of limitations and refinements of exponential models.

---

## P7 — Differentiation

### P7.1  *(AS part)*
- **Label:** Derivatives & first principles
- **AS:** sub-skills 1–3 and 5 (first principles for sin/cos and convexity are Year 2)
- **⚠ Grain check:** 6 sub-skills — the densest Pure node. This follows the spec's own clauses; 'Derivative as gradient' and 'Sketching the gradient function' could merge.
- **Sub-skills:**
  - Derivative as gradient & rate of change
  - Sketching the gradient function
  - Differentiation from first principles (xⁿ)
  - First principles for sin x & cos x
  - Second derivatives
  - Convex & concave curves, points of inflection
- **Spec:** Understand and use the derivative of f(x) as the gradient of the tangent to the graph of y = f(x) at a general point (x, y); the gradient of the tangent as a limit; interpretation as a rate of change sketching the gradient function for a given curve second derivatives differentiation from first principles for small positive integer powers of x and for sinx and cosx Understand and use the second derivative as the rate of change of gradient; connection to convex and concave sections of curves and points of inflection.

### P7.2  *(AS part)*
- **Label:** Differentiating standard functions
- **AS:** sub-skill 1 (the rest are Year 2)
- **⚠ Grain check:** Merge the exponential and ln x sub-skills if they're one lesson for you.
- **Sub-skills:**
  - Differentiating xⁿ (rational n)
  - Differentiating eᵏˣ & aᵏˣ
  - Differentiating sin kx, cos kx & tan kx
  - Differentiating ln x
- **Spec:** *(typed)* Differentiate xⁿ, for rational values of n, and related constant multiples, sums and differences. Differentiate eᵏˣ and aᵏˣ, sin kx, cos kx, tan kx and related sums, differences and constant multiples. Understand and use the derivative of ln x.

### P7.3  *(AS part)*
- **Label:** Applications of differentiation
- **AS:** all except points of inflection
- **Sub-skills:**
  - Tangents & normals
  - Stationary points (maxima & minima)
  - Points of inflection
  - Increasing & decreasing functions
- **Spec:** Apply differentiation to find gradients, tangents and normals maxima and minima and stationary points. points of inflection Identify where functions are increasing or decreasing.

### P7.4
- **Label:** Chain, product & quotient rules
- **⚠ Grain check:** 5 sub-skills; the three rules are separate lessons, rates of change usually its own. Merge the inverse-function sub-skill into the chain rule if you teach it there.
- **Sub-skills:**
  - Chain rule
  - Product rule
  - Quotient rule
  - Connected rates of change
  - Differentiating inverse functions (dx/dy)
- **Spec:** Differentiate using the product rule, the quotient rule and the chain rule, including problems involving connected rates of change and inverse functions.

### P7.5
- **Label:** Implicit & parametric differentiation
- **Sub-skills:**
  - Implicit differentiation
  - Parametric differentiation
- **Spec:** Differentiate simple functions and relations defined implicitly or parametrically, for first derivative only.

### P7.6
- **Label:** Forming differential equations
- **Sub-skills:**
  - Constructing differential equations
- **Spec:** Construct simple differential equations in pure mathematics and in context, (contexts may include kinematics, population growth and modelling the relationship between price and demand).

---

## P8 — Integration

### P8.1  *(AS)*
- **Label:** Fundamental Theorem of Calculus
- **Sub-skills:**
  - Fundamental Theorem of Calculus
- **Spec:** Know and use the Fundamental Theorem of Calculus

### P8.2  *(AS part)*
- **Label:** Integrating standard functions
- **AS:** sub-skill 1 (the rest are Year 2)
- **Sub-skills:**
  - Integrating xⁿ
  - Integrating eᵏˣ, 1/x, sin kx & cos kx
- **Spec:** *(typed)* Integrate xⁿ (excluding n = −1) and related sums, differences and constant multiples. Integrate eᵏˣ, 1/x, sin kx, cos kx and related sums, differences and constant multiples.

### P8.3  *(AS part)*
- **Label:** Definite integrals & area
- **AS:** sub-skill 1 (area between curves and parametric areas are Year 2)
- **⚠ Grain check:** sub-skill 3 comes from the spec's *Guidance* for 8.3 ("This includes curves defined parametrically"), not its Content — added 2026-10-10 because parametric integration had no home otherwise.
- **Sub-skills:**
  - Definite integrals & area under a curve
  - Area between two curves
  - Area under a parametric curve
- **Spec:** Evaluate definite integrals; use a definite integral to find the area under a curve and the area between two curves

### P8.4
- **Label:** Integration as the limit of a sum
- **Sub-skills:**
  - Integration as the limit of a sum
- **Spec:** Understand and use integration as the limit of a sum.

### P8.5
- **Label:** Integration by substitution & by parts
- **Sub-skills:**
  - Integration by substitution
  - Integration by parts
- **Spec:** Carry out simple cases of integration by substitution and integration by parts; understand these methods as the inverse processes of the chain and product rules respectively (Integration by substitution includes finding a suitable substitution and is limited to cases where one substitution will lead to a function which can be integrated; integration by parts includes more than one application of the method but excludes reduction formulae.)

### P8.6
- **Label:** Integration using partial fractions
- **Sub-skills:**
  - Integration using partial fractions
- **Spec:** Integrate using partial fractions that are linear in the denominator.

### P8.7
- **Label:** Separable differential equations
- **Sub-skills:**
  - Separating variables (incl. particular solutions)
- **Spec:** Evaluate the analytical solution of simple first order differential equations with separable variables, including finding particular solutions (Separation of variables may require factorisation involving a common factor.)

### P8.8
- **Label:** Differential equations in context
- **Sub-skills:**
  - Interpreting solutions in context
- **Spec:** Interpret the solution of a differential equation in the context of solving a problem, including identifying limitations of the solution; includes links to kinematics.

---

## P9 — Numerical methods

### P9.1
- **Label:** Locating roots
- **Sub-skills:**
  - Change of sign (incl. when it fails)
- **Spec:** *(typed)* Locate roots of f(x) = 0 by considering changes of sign of f(x) in an interval of x on which f(x) is sufficiently well behaved. Understand how change of sign methods can fail.

### P9.2
- **Label:** Iteration
- **Sub-skills:**
  - Iterative methods xₙ₊₁ = g(xₙ)
  - Cobweb & staircase diagrams
- **Spec:** Solve equations approximately using simple iterative methods; be able to draw associated cobweb and staircase diagrams.

### P9.3
- **Label:** Newton–Raphson
- **Sub-skills:**
  - Newton–Raphson (incl. when it fails)
- **Spec:** *(typed)* Solve equations using the Newton-Raphson method and other recurrence relations of the form xₙ₊₁ = g(xₙ). Understand how such methods can fail.

### P9.4
- **Label:** Trapezium rule
- **Sub-skills:**
  - Trapezium rule (incl. over- & under-estimates)
- **Spec:** Understand and use numerical integration of functions, including the use of the trapezium rule and estimating the approximate area under a curve and limits that it must lie between.

### P9.5
- **Label:** Numerical methods in context
- **Sub-skills:**
  - Numerical methods in context
- **Spec:** Use numerical methods to solve problems in context.

---

## P10 — Vectors

### P10.1  *(AS part)*
- **Label:** Vectors in 2D & 3D
- **AS:** sub-skill 1 (3D is Year 2)
- **Sub-skills:**
  - Vectors in 2D
  - Vectors in 3D
- **Spec:** Use vectors in two dimensions and in three dimensions

### P10.2  *(AS)*
- **Label:** Magnitude & direction
- **Sub-skills:**
  - Magnitude & direction (component ↔ magnitude–direction form)
- **Spec:** Calculate the magnitude and direction of a vector and convert between component form and magnitude/direction form.

### P10.3  *(AS)*
- **Label:** Vector addition & scalar multiplication
- **Sub-skills:**
  - Adding vectors & multiplying by scalars
- **Spec:** Add vectors diagrammatically and perform the algebraic operations of vector addition and multiplication by scalars, and understand their geometrical interpretations.

### P10.4  *(AS)*
- **Label:** Position vectors
- **Sub-skills:**
  - Position vectors & distance between points
- **Spec:** Understand and use position vectors; calculate the distance between two points represented by position vectors.

### P10.5  *(AS)*
- **Label:** Vector problems
- **Sub-skills:**
  - Vectors in geometry & context (incl. forces)
- **Spec:** Use vectors to solve problems in pure mathematics and in context (including forces).

---

## S1 — Statistical sampling

### S1.1  *(AS)*
- **Label:** Sampling
- **⚠ Grain check:** the list of methods in sub-skill 2 is from the spec's *Guidance* column, not its Content (Content names only random and opportunity sampling).
- **Sub-skills:**
  - Populations, samples & census
  - Sampling methods (random, stratified, systematic, quota, opportunity)
  - Critiquing sampling methods
- **Spec:** Understand and use the terms ‘population’ and ‘sample’. Use samples to make informal inferences about the population. Understand and use sampling techniques, including simple random sampling and opportunity sampling. Select or critique sampling techniques in the context of solving a statistical problem, including understanding that different samples can lead to different conclusions about the population.

---

## S2 — Data presentation and interpretation

### S2.1  *(AS)*
- **Label:** Single-variable data diagrams
- **⚠ Grain check:** sub-skill 2 is from the spec's *Guidance* column, not its Content.
- **Sub-skills:**
  - Histograms (area = frequency)
  - Box plots, cumulative frequency & frequency polygons
- **Spec:** Interpret diagrams for single-variable data, including understanding that area in a histogram represents frequency. Connect to probability distributions.

### S2.2  *(AS)*
- **Label:** Correlation & regression
- **Sub-skills:**
  - Scatter diagrams & regression lines (interpolation vs extrapolation)
  - Interpreting correlation (not causation)
- **Spec:** Interpret scatter diagrams and regression lines for bivariate data, including recognition of scatter diagrams which include distinct sections of the population (calculations involving regression lines are excluded). Understand informal interpretation of correlation. Understand that correlation does not imply causation.

### S2.3  *(AS)*
- **Label:** Averages & spread
- **⚠ Grain check:** 4 sub-skills; 3 and 4 are from the spec's *Guidance* column, not its Content but are usually lessons of their own. Merge 1 into 2 if you prefer.
- **Sub-skills:**
  - Mean, median, mode & range
  - Variance & standard deviation (incl. summary statistics)
  - Percentiles & interpolation from grouped data
  - Coding
- **Spec:** Interpret measures of central tendency and variation, extending to standard deviation. Be able to calculate standard deviation, including from summary statistics.

### S2.4  *(AS)*
- **Label:** Outliers & data cleaning
- **⚠ Grain check:** Three short skills, often taught alongside the large data set; merge if they're one lesson for you.
- **Sub-skills:**
  - Identifying outliers
  - Choosing & critiquing data presentation
  - Cleaning data
- **Spec:** Recognise and interpret possible outliers in data sets and statistical diagrams. Select or critique data presentation techniques in the context of a statistical problem. Be able to clean data, including dealing with missing data, errors and outliers.

---

## S3 — Probability

### S3.1  *(AS)*
- **Label:** Mutually exclusive & independent events
- **Sub-skills:**
  - Mutually exclusive & independent events
- **Spec:** Understand and use mutually exclusive and independent events when calculating probabilities. Link to discrete and continuous distributions.

### S3.2
- **Label:** Conditional probability
- **Sub-skills:**
  - Conditional probability with tree diagrams, Venn diagrams & two-way tables
  - Conditional probability formula & set notation
- **Spec:** *(typed)* Understand and use conditional probability, including the use of tree diagrams, Venn diagrams, two-way tables. Understand and use the conditional probability formula P(A|B) = P(A ∩ B) / P(B).

### S3.3
- **Label:** Modelling with probability
- **Sub-skills:**
  - Modelling with probability (critiquing assumptions)
- **Spec:** Modelling with probability, including critiquing assumptions made and the likely effect of more realistic assumptions.

---

## S4 — Statistical distributions

### S4.1  *(AS)*
- **Label:** Binomial distribution
- **Sub-skills:**
  - Discrete probability distributions (incl. discrete uniform)
  - Binomial distribution B(n, p)
- **Spec:** Understand and use simple, discrete probability distributions (calculation of mean and variance of discrete random variables is excluded), including the binomial distribution, as a model; calculate probabilities using the binomial distribution.

### S4.2
- **Label:** Normal distribution
- **⚠ Grain check:** sub-skills 2 and 3 are from the spec's *Guidance* column, not its Content; each is usually its own lesson.
- **Sub-skills:**
  - Normal probabilities (calculator)
  - Finding an unknown μ or σ
  - Normal approximation to the binomial (continuity correction)
- **Spec:** Understand and use the Normal distribution as a model; find probabilities using the Normal distribution Link to histograms, mean, standard deviation, points of inflection and the binomial distribution.

### S4.3
- **Label:** Choosing a distribution
- **Sub-skills:**
  - Choosing binomial or Normal models
- **Spec:** Select an appropriate probability distribution for a context, with appropriate reasoning, including recognising when the binomial or Normal model may not be appropriate.

---

## S5 — Statistical hypothesis testing

### S5.1  *(AS part)*
- **Label:** Hypothesis testing: language & correlation
- **AS:** sub-skill 1 (correlation tests are Year 2)
- **Sub-skills:**
  - Language of hypothesis testing (H₀, H₁, significance level, critical region, p-value)
  - Hypothesis tests for correlation (ρ)
- **Spec:** Understand and apply the language of statistical hypothesis testing, developed through a binomial model: null hypothesis, alternative hypothesis, significance level, test statistic, 1-tail test, 2-tail test, critical value, critical region, acceptance region, p-value; extend to correlation coefficients as measures of how close data points lie to a straight line. and be able to interpret a given correlation coefficient using a given p-value or critical value (calculation of correlation coefficients is excluded).

### S5.2  *(AS)*
- **Label:** Binomial hypothesis tests
- **Sub-skills:**
  - Binomial hypothesis tests (1- & 2-tail, critical regions)
- **Spec:** Conduct a statistical hypothesis test for the proportion in the binomial distribution and interpret the results in context. Understand that a sample is being used to make an inference about the population and appreciate that the significance level is the probability of incorrectly rejecting the null hypothesis.

### S5.3
- **Label:** Normal hypothesis tests
- **Sub-skills:**
  - Hypothesis test for a Normal mean (X̄ ~ N(μ, σ²/n))
- **Spec:** Conduct a statistical hypothesis test for the mean of a Normal distribution with known, given or assumed variance and interpret the results in context.

---

## M6 — Quantities and units in mechanics

### M6.1  *(AS)*
- **Label:** Quantities & units
- **Sub-skills:**
  - SI units & unit conversion
- **Spec:** Understand and use fundamental quantities and units in the S.I. system: length, time, mass. Understand and use derived quantities and units: velocity, acceleration, force, weight, moment.

---

## M7 — Kinematics

### M7.1  *(AS)*
- **Label:** Language of kinematics
- **Sub-skills:**
  - Displacement, velocity, speed & acceleration
- **Spec:** Understand and use the language of kinematics: position; displacement; distance travelled; velocity; speed; acceleration.

### M7.2  *(AS)*
- **Label:** Kinematics graphs
- **Sub-skills:**
  - Displacement–time graphs
  - Velocity–time graphs (gradient & area)
- **Spec:** Understand, use and interpret graphs in kinematics for motion in a straight line: displacement against time and interpretation of gradient; velocity against time and interpretation of gradient and area under the graph.

### M7.3  *(AS part)*
- **Label:** Constant acceleration (suvat)
- **AS:** sub-skill 1 (vectors are Year 2)
- **Sub-skills:**
  - suvat in a straight line (incl. derivation)
  - suvat with vectors (2D)
- **Spec:** Understand, use and derive the formulae for constant acceleration for motion in a straight line. Extend to 2 dimensions using vectors.

### M7.4  *(AS part)*
- **Label:** Variable acceleration (calculus)
- **AS:** sub-skill 1 (vectors are Year 2)
- **Sub-skills:**
  - Variable acceleration in a straight line
  - Variable acceleration with vectors (2D)
- **Spec:** *(typed)* Use calculus in kinematics for motion in a straight line: v = dr/dt, a = dv/dt = d²r/dt²; r = ∫ v dt, v = ∫ a dt. Extend to 2 dimensions using vectors.

### M7.5
- **Label:** Projectiles
- **Sub-skills:**
  - Projectiles (time of flight, range, greatest height)
- **Spec:** Model motion under gravity in a vertical plane using vectors; projectiles.

---

## M8 — Forces and Newton’s laws

### M8.1  *(AS)*
- **Label:** Forces & Newton's first law
- **Sub-skills:**
  - Forces & Newton's first law
- **Spec:** Understand the concept of a force; understand and use Newton’s first law.

### M8.2  *(AS part)*
- **Label:** Newton's second law (F = ma)
- **AS:** sub-skill 1 (resolving is Year 2)
- **⚠ Grain check:** 'inclined planes' is from the spec's *Guidance* column, not its Content.
- **Sub-skills:**
  - F = ma in a straight line (incl. forces as vectors)
  - F = ma with resolved forces (incl. inclined planes)
- **Spec:** Understand and use Newton’s second law for motion in a straight line (restricted to forces in two perpendicular directions or simple cases of forces given as 2-D vectors); extend to situations where forces need to be resolved (restricted to 2 dimensions).

### M8.3  *(AS)*
- **Label:** Weight & motion under gravity
- **Sub-skills:**
  - Weight & vertical motion under gravity
- **Spec:** Understand and use weight and motion in a straight line under gravity; gravitational acceleration, g, and its value in S.I. units to varying degrees of accuracy. (The inverse square law for gravitation is not required and g may be assumed to be constant, but students should be aware that g is not a universal constant but depends on location.)

### M8.4  *(AS part)*
- **Label:** Newton's third law & connected particles
- **AS:** sub-skills 1–2 (resolving is Year 2)
- **Sub-skills:**
  - Equilibrium & Newton's third law
  - Connected particles (pulleys, lifts)
  - Resolving forces & equilibrium under coplanar forces
- **Spec:** Understand and use Newton’s third law; equilibrium of forces on a particle and motion in a straight line (restricted to forces in two perpendicular directions or simple cases of forces given as 2-D vectors); application to problems involving smooth pulleys and connected particles; resolving forces in 2 dimensions; equilibrium of a particle under coplanar forces.

### M8.5
- **Label:** Resultant forces
- **Sub-skills:**
  - Resultant forces & dynamics in a plane
- **Spec:** Understand and use addition of forces; resultant forces; dynamics for motion in a plane.

### M8.6
- **Label:** Friction
- **Sub-skills:**
  - Friction & limiting equilibrium (F ≤ μR)
  - Motion on rough surfaces (F = μR)
- **Spec:** Understand and use the F ≤µR model for friction; coefficient of friction; motion of a body on a rough surface; limiting friction and statics.

---

## M9 — Moments

### M9.1
- **Label:** Moments
- **⚠ Grain check:** sub-skill 2 is from the spec's *Guidance* column, not its Content ('Equilibrium of rigid bodies… e.g. ladder problems').
- **Sub-skills:**
  - Moments with parallel forces (e.g. beams)
  - Rigid bodies with non-parallel forces (e.g. ladders)
- **Spec:** Understand and use moments in simple static contexts.
