# 20250714_Presentation_for_Webinar_on_MachineLearning

## Page 1
# Machine Learning in Reserving

## Introduction and Recent Developments

Jacky Poon, FIAA, GAICD, #datascienceactuary
*On behalf of the Machine Learning in Reserving Working Party (IFoA)*
14 July 2025
![Page 1 Image 1](202507_Webinar_Machine_Learning_in_Reserving_assets/20250714_Presentation_for_Webinar_on_MachineLearning_p01_img1.jpg)
![Page 1 Image 2](202507_Webinar_Machine_Learning_in_Reserving_assets/20250714_Presentation_for_Webinar_on_MachineLearning_p01_img2.jpg)

## Page 2
# Welcome to the Webinar We will begin shortly 

## A few housekeeping items before we begin:

1. Questions \& Comments - Verbal capabilities have been turned off however questions or comments can be submitted by clicking on the Q\&A icon at the bottom of your screen. All questions will be answered during the Q\&A session at the end of the presentations.
2. Recording and presentation - A YouTube recording along with the presentation will be made available on the IAA website within the next day or so. They can be found where the paper has been posted under Publications/Papers on the IAA website at www.actuaries.org .

## Page 3
# Welcome and thank you for joining today's webinar. 

## Disclaimer Note:

Any views or opinions expressed in this presentation and in the Q\&A session are solely those of the authors/presenters and do not necessarily reflect the policies or positions of the International Actuarial Association (IAA). While every effort has been made to ensure the accuracy and completeness of the material, the IAA and authors give no warranty in that regard and reject any responsibility or liability for any loss or damage incurred through the use of, or reliance upon, the information contained therein.

## Page 4
# Introduction 

"Why machine learning in claims reserving?"

## Page 5
# About the IFoA Machine Learning in Reserving Working Party 

- Volunteers from around the world
- Help actuaries gain Machine Learning ("ML") skills with Foundations page \& resources
- Providing code and explanations - "try this at home"
- Neural Network ("NN") framework - making NNs accessible.

We want companies to take and apply to their own data and feedback findings

## Page 6
# Why Machine Learning in Claims Reserving? 

- Use all of the data: potential to be more accurate in a big data world? If results show it is a more predictive model, is that a case to use it?
- Granular predictions: level of detail to support actionable insights e.g.
- Pricing - better estimate of claims when drilling down into segments
- Claims analytics - support fraud modelling and cost containment efforts
- Diagnostics exist for "black box" models: SHAP, LIME, PDP
- Can act as early warning system - detecting changes in trend
"A practical introduction to using neural networks in reserving on individual claims data": https://institute-and-faculty-of-actuaries.github.io/mlr-blog/post/research/icnn-2024-02-covering/

## Page 7
# Potential for Neural Networks 

Within the working party, we are exploring Neural Networks heavily. Here's why:

## Advantages:

- Residual networks generalize GLMs
- Used in state-of-the-art models for e.g. image, text, audio transcriptions
- Transformers quite powerful for sequence data generally
- Entity embeddings can effectively model categorical variables
- Output probability distributions with mixture density


## Issues to consider:

- In time series, simpler models often perform as well as neural networks ("Are Transformers Effective for Time Series Forecasting?" A. Zeng et al)
- With tabular-only data, gradient boosted decision trees are often easy to calibrate to a good result.
- Random initialization may lead to variance in model predictions
- Complexity vs simpler models

## Page 8
# Learning about Machine Learning 

"It is difficult to find time and resources to develop these skills..."

## Page 9
# Learning Python (Quickly) 

## Basic Python and Data Wrangling

Download Visual Studio Code, a free code editor by Microsoft and follow steps in their YouTube tutorial for "VSCode Jupyter". Follow Chapters 1-11 in "Automate the Boring Stuff" is a free-to-read resource on Python.
Read my (largely Al generated) gist on List Comprehensions and if familiar with SQL, a translation from SQL to pandas logic.

## Use Al to help

Claude by Anthropic and Google Gemini in Google AI Studio are excellent at coding. Be specific and define the format of your input data. Ask the LLM to generate test data and tests and diagnostics on outputs.

Potential: Ability to automate processes and free up time

## Page 10
# Developing ML skills 

I (and volunteers from the YDAWG and DSAIPC) have a cookbook:
https://actuariesinstitute.github.io/cookbook/docs/index.html
Vikram's intro: https://institute-and-faculty-of-actuaries.github.io/mlr-blog/post/foundations/2025-02python/
Relevant sections:

- Regression, Classification and Technical Price
- Workflow Management


## Exercises:

With help from AI, read the cookbook sections and build a Streamlit App to do a full Exploratory Data Analysis and a regression model on this dataset used in the SHAP article.
Work through https://institute-and-faculty-of-actuaries.github.io/mlr-blog/post/foundations/pythonglms/

## Page 11
# Basics of Machine Learning in Reserving 

Basic ideas in our approach

## Page 12
# Getting started with MLRWP 

## We have a blog:

https://institute-and-faculty-of-actuaries.github.io/mlr-blog/

- Learning resources for beginners with Foundations page
- Latest research for experienced practitioners
- Providing code and explanations: designed for you to able to download and use on your own data.

And a book!
https://mlrwp.github.io/mlrwp-book/
Mostly in R

## Page 13
# Simulated data - SPLICE 

- Problem: There is a lack of real-world datasets to test and benchmark new machine learning reserving techniques.
- Solution: The SPLICE paper presents a framework and a free R package to generate realistic, synthetic claims data.
- Key Advantage: The synthetic data allows researchers to introduce specific challenges to test how well models respond. Benchmark different models in specific claim scenarios.
- Technical Innovation: SPLICE extends a previous package by adding customisable simulations of case estimates, based on realistic actuarial principles.

## Page 14
# Tabular based models: *Triangles are tables and chain ladder is a GLM*

#### **There is a GLM form of chain ladder:**

- Log link, over-dispersed Poisson
- *Incremental Payments ~ Occurrence Period + Development Period*
- Occurrence Period and Development Period are one-hot encoded (1-0 flags for occurrence and development period = n, n=1...N)
- See https://institute-and-faculty-of-actuaries.github.io/mlr-blog/post/foundations/python-glms/
![Page 14 Image 1](202507_Webinar_Machine_Learning_in_Reserving_assets/20250714_Presentation_for_Webinar_on_MachineLearning_p14_img1.jpg)
![Page 14 Image 2](202507_Webinar_Machine_Learning_in_Reserving_assets/20250714_Presentation_for_Webinar_on_MachineLearning_p14_img2.jpg)

## Page 15
# Tabular data format

- Tabular approaches - convert the claims data to a tabular format
- Simplest example (right):
- X: Accident, Development and Calendar Periods
- y: Payment in the Acc/Dev period.
- Example table right is an aggregated dataset but can also expand to individual claim or policy dataset.

|  Accident
Period | Dev.
Period | Cal. Period | Claims
Paid  |
| --- | --- | --- | --- |
|  1 | 1 | 1 | $\$ x x$  |
|  1 | 2 | 2 | $\$ x x$  |
|  1 | 3 | 3 | $\$ x x$  |
|  1 | 4 | 4 | $\$ x x$  |
|  2 | 1 | 2 | $\$ x x$  |
|  2 | 2 | 3 | $\$ x x$  |
|  2 | 3 | 4 | $\$ x x$  |
|  2 | 4 | 5 | $\$ x x$  |
|  $\ldots$ | $\ldots$ | $\ldots$ |   |

## Page 16
# Tabular based models 

## Other regression models can replace GLMs

- Basic GBM, Neural Networks ("NN") or LASSO GLM on triangle data: https://institute-and-faculty-of-actuaries.github.io/mlr-blog/post/foundations/scikitexample/
- How GLMs are a special case of NN: https://owars.info/mario/2020 Wuthrich.pdf
- Example starting from a chain ladder and showing steps to get to a individual, probabilistic neural network model: https://institute-and-faculty-of-actuaries.github.io/mlr-blog/post/research/chain ladder to individual mdn/
- More advanced triangle methods than Chain Ladder? Could have NN analogues: "Penalising Unexplainability in Neural Networks for Predicting Payments per Claim Incurred" (Poon 2019) on individual policy, claim count and claim amount data

## Page 17
# Sequence based models

- Claims histories are also sequences:


- Sequence based models such as GRU, LSTM, Transformers may be relevant
- Current area of focus
![Page 17 Image 1](202507_Webinar_Machine_Learning_in_Reserving_assets/20250714_Presentation_for_Webinar_on_MachineLearning_p17_img1.jpg)
![Page 17 Image 2](202507_Webinar_Machine_Learning_in_Reserving_assets/20250714_Presentation_for_Webinar_on_MachineLearning_p17_img2.jpg)

## Page 18
# Calibrating and diagnostics

## The blogs

- **Explainer**: Takes code to implement a neural network and steps you through / explains what it is doing.
- **Diagnostics**: Provides examples of outputs you can use to understand what the model is doing and assess its effectiveness. Gives details of some of the different tools you can use to produce them, and steps you through how to create them. We intend to add to the Diagnostics blog over time.


- **Hyperparameters**: Takes individual hyperparameters, shows what happens when you vary them and steps you through how to change them in the code so you can have a go yourself.
![Page 18 Image 1](202507_Webinar_Machine_Learning_in_Reserving_assets/20250714_Presentation_for_Webinar_on_MachineLearning_p18_img1.jpg)
![Page 18 Image 2](202507_Webinar_Machine_Learning_in_Reserving_assets/20250714_Presentation_for_Webinar_on_MachineLearning_p18_img2.jpg)
![Page 18 Image 3](202507_Webinar_Machine_Learning_in_Reserving_assets/20250714_Presentation_for_Webinar_on_MachineLearning_p18_img3.jpg)
![Page 18 Image 4](202507_Webinar_Machine_Learning_in_Reserving_assets/20250714_Presentation_for_Webinar_on_MachineLearning_p18_img4.jpg)

## Page 19
# Generative AI and NLP

- Claims diaries often include unstructured data. But this does not prevent us from data miningâ€?
- Traditional approach is to have freeform text to be converted to model features with bag of words, embeddings:

https://actuariesinstitute.github.io/cookbook/docs/DAA_M07_CS1.html

- Can be applied to identify keywords that drive claims cost
- Not the main focus of the MLR WP but can add more predictive features in the application.

|  Words driving complaints: |   |
| --- | --- |
|  Word | Weight  |
|  worst | 1.7  |
|  horrible | 1.7  |
|  rude | 1.6  |
|  terrible | 1.6  |
|  avoid | 1.4  |
|  poor | 1.3  |
|  beware | 1.1  |
|  unprofessional | 0.9  |
|  disappointed | 0.9  |
|  elsewhere | 0.9  |

|  Words driving non-complaints: |   |
| --- | --- |
|  Word | Weight  |
|  excellent | -1.5  |
|  amazing | -1.4  |
|  awesome | -1.4  |
|  thank | -1.4  |
|  great | -1.3  |
|  best | -1.3  |
|  highly | -1.2  |
|  honest | -1.2  |
|  quick | -1.2  |
|  fair | -1.2  |

Machine Learning in Reserving: Introduction and Recent Developments - 14 July 2025
![Page 19 Image 1](202507_Webinar_Machine_Learning_in_Reserving_assets/20250714_Presentation_for_Webinar_on_MachineLearning_p19_img1.jpg)

## Page 20
# Generative AI and NLP

Large language models can also "read" freeform text (such as claim diaries) and create structured features based on the text. Cookbook example â€?reading freeform text from reviews: https://actuariesinstitute.github.io/cookbook/docs/py_llm_text_sentiment.html

|  Excellent value. | I used this travel insurance mainly for  |
| --- | --- |
|  Great service | We took out a cover more policy for  |
|  Stay Away from CBA Allianz Travel In | My wife developed a medical condition  |
|  Peace of mind should any problems | Prices getting more expensive as we  |
|  made a claim | needed to make a claim when I had  |
|  Refund do to accident | Due to my accident four days prior to  |
|  Good coverage, good value for money | We use AI for our car rental excess  |
|  Would never travel o/s without it! | We have booked insurance through  |
|  Comprehensive Travel Insurance to S | Policy was easily and quickly accessed  |
|  Make sure you don't misplaced your | We took out cruise insurance for a response  |
|  Terrible | please please please do not get insurance  |
|  Perfect choice for travelers | Great Value, very easy to get full coverage  |
|  Sensational service | While Overseas my husband became  |
|  Unlucky if you break a surfboard while | If you are surfing, use another company  |
|  Best motorbike travel insurance | Good value travel insurance, which is  |
|  Happy traveler and TID holder | Have used TID before, never had a problem  |
|  Travel insurance | I didn't make a claim and therefore can  |
|  S out of S | This is the first time I have used Budy  |
![Page 20 Image 1](202507_Webinar_Machine_Learning_in_Reserving_assets/20250714_Presentation_for_Webinar_on_MachineLearning_p20_img1.jpg)
![Page 20 Image 2](202507_Webinar_Machine_Learning_in_Reserving_assets/20250714_Presentation_for_Webinar_on_MachineLearning_p20_img2.jpg)

## Page 21
# Applications of Machine Learning Reserving 

With some example scenarios

## Page 22
# We use models to solve actual business problems...

Some examples of real-world inspired scenarios where a granular ML model form may be useful
![Page 22 Image 1](202507_Webinar_Machine_Learning_in_Reserving_assets/20250714_Presentation_for_Webinar_on_MachineLearning_p22_img1.jpg)

## Page 23
# Example: Mix Effects 

## Scenario:

- The portfolio mix has shifted significantly in recent years across a number of dimensions (e.g. age, product tier, region). To complicate matters further, your product team advise that different covers \& demographics are likely to have claims that develop at different rates.
- Questions have been raised whether the mix change is triggering adverse selection and affecting how the portfolio develops


## Potential angles of exploration:

- Use pricing/risk factors as dimension into granular claim model
- Copy and extend pricing model to capture reserving effects (e.g. dev period 1 claims as predictor for ultimate)

## Page 24
# Example: Processing speed issue 

## Scenario:

- Paid is unusually high but faster processing may be a contributor
- Not enough history to see this in triangles, but other corroborating operational data metrics


## Potential angles of exploration:

- Rely on forecast? (which may or may not have ML elements)
- Build model predicting costs based on operational processing metrics

## Page 25
# Example: Case Estimation 

## Scenario:

- Case reserves are important for the portfolio due to large claims contributing a high proportion of costs.
- However, although there are detailed case notes, the case reserves set by claims team are inexplicably (or explicably) unreliable.


## Potential angles of exploration:

- Use LLMs to create structured fields from case notes.
- Build a granular model to create own case estimate model.
- Explore further drivers for variances with claims team, or use own case estimate for incurred calculation.

## Page 26
# The MLR-WP 

Current focus and our own research

## Page 27
# Getting up to speed with research 

A brief history of papers looking at using neural networks in reserving (up to 2021)
https://institute-and-faculty-of-actuaries.github.io/mlr-blog/post/literature-review/nn-cas2020/index.html

We also have a MLRWP Journal Club!

## Page 28
# Areas of focus 

- Creating and sharing development resources
- Sequence based models
- Diagnostics
- Keeping abreast of literature - replication and comparisons

## Page 29
# Call to action 

MLRWP is a volunteer group - often in spare time
Need support from businesses to increase speed of progress

We are looking for more people to help. Have more ideas than we do manpower!

## What can you do next?

## Page 30
# Q\&A Session 

Should you have any questions or comments, please add them to the Q\&A icon at the bottom of your screen.

## Page 31
# Thank you for joining today's webinar! 

Should you have any further questions or comments, please send them directly to Technical Activities of the IAA at the following email address:
technical.activities@actuaries.org


