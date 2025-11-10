# AITF_Documentation_AIModels_ConsultationDraft

## Page 1
# Documentation of Artificial Intelligence Models

**AI Task Force**

**July 2025**

*(Consultation Draft)*
![Page 1 Image 1](202507_Documentation_of_Artificial_Intelligence_Models_assets/AITF_Documentation_AIModels_ConsultationDraft_p01_img1.jpg)

## Page 2
# IAA Paper 

## Documentation of Artificial Intelligence Models

(Consultation Draft)

This paper was prepared by the Artificial Intelligence (AI) Task Force of the International Actuarial Association (IAA).

The IAA is the worldwide association of professional actuarial associations, with several special interest sections and working groups for individual actuaries. The IAA exists to encourage the development of a global profession, acknowledged as technically competent and professionally reliable, which will ensure that the public interest is served.

The role of the AI Task Force is to deliver on the Statement of Intent for IAA Activities on Artificial Intelligence (SOI) as adopted by Council on 8 March 2024

The paper was authored by a drafting group appointed by the AI Task Force.
[Wording to be added to the final version: This paper has been approved for IAA publication by the AI Task Force and the Executive Committee in accordance with the IAA's Communications Policy.]

This paper is published by the IAA solely to encourage understanding and debate of the issues raised therein. For the avoidance of any doubt, this is not an International Standard of Actuarial Practice (ISAP), nor does it set standards or requirements which any individual or organization is expected to consider or observe, or with which they are expected to comply. This is the case notwithstanding any language in the paper which, but for this clause, might suggest otherwise. This statement takes precedence over any such wording

Tel: +1-613-236-0886 Fax: +1-613-236-1386
Email: secretariat@actuaries.org
605 - 75 Albert St, Ottawa ON K1P 5E7 Canada
www.actuaries.org

[^0]
[^0]:    (c) International Actuarial Association/ Association Actuarial Internationale
![Page 2 Image 1](202507_Documentation_of_Artificial_Intelligence_Models_assets/AITF_Documentation_AIModels_ConsultationDraft_p02_img1.jpg)

## Page 3
# Table of Contents 

1. Introduction ..... 1
2. Data ..... 1
3. Model Development ..... 2
4. Model Deployment and Maintenance ..... 4
5. User Guide ..... 5
6. Other Disclosures ..... 5
References ..... 8

## Page 4
# 1. Introduction 

Documentation is a vital component of any AI model, forming the foundation for a robust model governance framework. Comprehensive model documentation is essential not only for compliance and regulatory purposes, but also for transparency, accountability of the AI models and continuity of operations.
While this paper aims to assist actuaries in creating effective documentation for their AI models, it makes no claim to be exhaustive. This paper outlines the key elements which may be considered as good practice for documentation of an AI model. The level of detail included in AI model documentation could vary depending on various factors, such as the level of significance, risk level and complexity of the AI models. Actuaries are encouraged to use professional judgement and tailor the documentation to these factors, with the goal of meeting the needs of the end users of the documentation. Note that throughout this document, the terms "AI", "AI systems", and "AI models" may be used interchangeably.
This paper is intended to be read in conjunction with the Artificial intelligence Governance Framework paper. ${ }^{1}$ It provides supplementary details specifically focused on documentation practices within the broader AI governance context. The primary audience includes model developers and individuals involved in validation during the model development stage.

## 2. Data

Data is a critical component of any AI system. With the increasing use of unstructured data and non-traditional data sources, comprehensive documentation is important for providing clarity, compliance and usability for actuarial work.
Actuaries could consider producing a data card, which is a structured document that provides essential information about datasets, to enable stakeholders to understand the data and make informed decisions abouts its application and the associated AI models.
Key components to consider when documenting data for an AI system are:
a. Data flow:

- Illustrate the data flow within the AI system, detailing each stage from data collection to data manipulation, feature engineering, model development and downstream model applications.
b. Data inventory:
- List all internal and external data sources used in the AI model.
- Specify the types of data utilized, including structured and unstructured formats.
- Provide detailed descriptions of data fields and associated metadata.
c. Data quality:
- Evaluate data quality based on key data governance principles (see Governance Framework ${ }^{2}$ for details).
- Document the processes and tools used for data validation, data cleaning and preprocessing, feature engineering, etc.

## Page 5
d. Data governance

- Identify data owners and stewards responsible for maintaining data quality and compliance (see Governance Framework ${ }^{3}$ for roles and responsibilities). This is especially important for actuaries providing third party vendor services.
- Clearly document access rights and any restrictions related to data usage.
e. Data usage
- Outline how the data will be used within the Al system, including any restrictions on data usage and the rationale behind these restrictions.
- Document any assumptions made regarding the use of the data.
f. Data Limitations and Weaknesses:
- Identify known data insufficiencies, including missing data, data that may be outdated, or data that lacks sufficient granularity for analysis.
- Document limitations in the data sources, such as potential biases, representativeness issues, or constraints in data collection methods (see Governance Framework ${ }^{4}$ for details on fairness and bias).
- Discuss the implications of these limitations on the analysis and decision-making processes, including how they may affect model performance, and the reliability of insights derived from the data.
- Document steps taken to mitigate any data limitations and weaknesses.
g. Compliance, ethics and legal considerations
- Document compliance to relevant data laws and regulations as well as the standards of practice of the actuarial bodies.
Address ethical implications of data usage, including fairness and bias, as well as the steps taken to identify and mitigate these biases.


# 3. Model Development 

Developing an Al model typically involves judgement especially with respect to the model training and model selection processes. Therefore, it is important to clearly document the details throughout the model development process.
Actuaries could consider producing a model card, which is a structured document that provides essential information about an Al model, to enable stakeholders to understand the model's capabilities and limitations.
Key components to consider include:
a. Model overview

- Clearly state the objective of the model and the specific problem statement.
- Define the scope of the model, including the target population and any model limitations. In the actuarial context, specify the functions for which the Al system is

## Page 6
designed. For example, an AI model developed to analyse policyholder behaviour for a specific insurance product may not be applicable to other types of insurance.

- State the model category (e.g. transparent, explainable, opaque) and model type (e.g. GLM, Neural Networks, LLM, etc.), (see Governance Framework ${ }^{5}$ for details).
- Clearly state model inputs, algorithms and outputs. Outline any dependencies on other models. Explain how the model interacts with or relies on other models and discuss how changes to these dependencies could affect the performance and reliability of the model.
- Outline the downstream end user and impact of the model application.
- Create a flowchart or model process diagram to visualise the model overview, if applicable.
- Document roles and responsibilities of individuals involved in the model life cycle (see Governance Framework ${ }^{6}$ for roles and responsibilities).
- Clarify ownership of the model. This is especially important for actuaries providing third party vendor services.
b. Model selection:
- Document the rationale behind the selection of algorithms used in the model, including any comparisons made between different approaches.
- Document the hyperparameters chosen, the tuning process, and the reasoning behind these choices.
c. Model training and validation
- Describe the training process, including the training dataset, validation techniques (e.g., cross-validation), and performance metrics used (see Governance Framework ${ }^{7}$ for validation of AI models).
- Detail how the dataset is split into training, validation, testing and hold out sets (if applicable); describe the cross-validation technique used, if applicable.
d. Model performance and evaluation:
- Clearly define metrics used to evaluate model performance (e.g., accuracy, precision vs recall, ROC-AUC, etc.), including explanation on how each metric is calculated with any threshold or criteria.
- Document the results of performance evaluations, including any benchmarking against baseline models or industry standards.
- Document any stress tests and sensitivity analysis conducted.
e. Model interpretation
- Document methods for interpreting model predictions, such as global feature importance analysis and local interpretation techniques like SHAP or LIME, to make the decision-making process of black-box models transparent for stakeholders, including developers, regulators, and end-users. (See Governance Framework ${ }^{8}$ for transparency and explainability.)

## Page 7
|  114 | - | Summarize key insights from the model and how they relate to the actuarial context.  |
| --- | --- | --- |
|  115 | f. Model limitation and assumptions |   |
|  116 | - | Clearly state the limitations of the model and the impact when applied in the real  |
|  117 | world, including assumptions made and potential biases. |   |
|  118 | g. Compliance, ethics and legal considerations |   |
|  119 | - | Check compliance with industry regulations and standards relevant to the model ap-  |
|  120 |  | plication. For models that require insurance regulators' approval, clearly state the sta-  |
|  121 |  | tus of the approval. Document compliance to relevant AI regulations and standards  |
|  122 |  | of practice of the actuarial bodies.  |
|  123 | - | Address ethical implications of model usage, including potential biases and fairness  |
|  124 |  | issues, as well as the steps taken to identify and mitigate these biases. Discuss the  |
|  125 |  | ethical considerations associated with the model. This is especially important for ac-  |
|  126 |  | tuarial work where most of the actuarial AI models has direct or indirect impact to  |
|  127 |  | consumers. Detail impact assessment of the model outcomes on different stakehold-  |
|  128 |  | ers.  |
|  129 | h. Version control and management |   |
|  130 | - | Maintain a version history and change log of the model which outlines the changes  |
|  131 |  | made, including updates, improvements and bug fixes.  |
|  132 | - | Discuss the impact and justification of the changes.  |
|  133 | - | Detail the model review and approval process.  |
|  134 | 4. Model Deployment and Maintenance |   |
|  135 | A proper deployment allows stakeholders to leverage the model's capability while minimizing as- |   |
|  136 | sociated risks. Additionally, on-going model maintenance helps keep the model relevant, accurate |   |
|  137 | and aligned with its intended purpose. It is recommended to address these two areas in the doc- |   |
|  138 | umentation. Recommended elements are listed below. For details on implementation and moni- |   |
|  139 | toring of AI models see Governance Framework Error! Reference source not found.. ${ }^{9}$ |   |
|  140 | a. | Deployment overview  |
|  141 | - | Summarize the deployment process and the associated technical requirements.  |
|  142 | - | Describe the environment where the model will be deployed, system architecture and  |
|  143 |  | infrastructure details.  |
|  144 | - | Create a flowchart or process diagram to visualize the deployment process, if appli-  |
|  145 |  | cable.  |
|  146 | b. | Deployment process  |
|  147 | - | Document the deployment strategy and process, including issues encountered and  |
|  148 |  | solutions.  |
|  149 | - | Document pre deployment testing, e.g. integration testing and user acceptance testi-  |
|  150 |  | ing.  |
|  151 | c. Version control |   |

## Page 8
- Maintain a version history of deployed models.
d. Monitoring and feedback loop
- Describe the plan for ongoing monitoring of model performance post-deployment, such as performance metrics post deployment and alert mechanisms.
- Specify frequency and methods of reviewing model performance.
- Include process for gathering feedback from users and stakeholders regarding model performance.
- Describe escalating processes established for the Al model; document issues identified, steps taken to investigate the issue, and the decisions made to address the issues.
e. Maintenance
- Outline model maintenance plan, such as model updates and quality checks.
- Specify frequency for model maintenance.
- Define criteria for model adjustments and model retraining (include process to retrain model if applicable).
- Define processes for implementing model updates and conducting quality checks, and document rationale for each update, whether regular or irregular.


# 5. User Guide 

It is also important to include a user guide on how to use and interact with the model. The user guide needs to be clear, structured and tailored to the need of the users, include practical examples as well as support resources.
It is recommended to include the following content in the user guide document:
a. Model overview, including its functionality and intended use cases.
b. Installation instructions and/or setup requirements to use the model.
c. How to navigate through the model (includes updating the input; running the model; and interpreting the output).
d. How to troubleshoot the models, such as including common issues and workarounds.
e. How to maintain and update the model.
f. Support and resources, if applicable.
g. Glossary, if applicable.

## 6. Other Disclosures

When documenting an Al model, particularly in the context of actuarial practice, it is crucial to include additional disclosures that address various model risks and considerations. The additional disclosures not only enhance transparency but also help model users and stakeholders make informed decisions.

## Page 9
Below are some additional disclosures that could become necessary depending on the models in different parts of the model documentation:
a. Model risk and limitation

- Summarize model risks including definition and description: explain potential adverse consequences that could arise from making decisions based on potential incorrect or misuse of the model output - which could include financial losses, regulatory violations or reputation risk.
- Elaborate on limitations of the model, including limitations around model assumptions, scope of model application, model performance under different conditions. For instance, in the context of insurance, it is important to document if an Al model is built for a specific line of business or specific demographic and hence would not be appropriate to be used for different situations or conditions.
b. Data privacy
- Document data privacy considerations to address how the model handles personal or sensitive data. It is important to discuss compliance with existing regulations and any measures taken to protect individual data privacy.
- Describe any methods used to anonymize or pseudonymize data to mitigate potential privacy risks.
c. Data security
- Outline the security protocols in place to protect data from unauthorized access or breaches.
- Specify access controls for individuals for the Al system from end to end.
- Detail any encryption methods used to secure data during storage, model production and transmission.
d. Outcomes of key function activities
- Document the outcomes of key function activities related to the Al model, e.g.
i. Risk assessment performed by Risk Management function including a comprehensive report detailing the findings and recommendations.
ii. Internal audit reports, including assessments of compliance and the effectiveness of the Al model and its associated processes, provide valuable insights into the model's operational integrity and risk profile. It is recommended that these reports be included in the documentation so that stakeholders have access to relevant evaluations and conclusions.
e. References and resources
- Provide references for any research, methodologies, or framework referenced in the documentation.
- Reference any supplementary materials that may assist users in understanding the model. For example, references to actuarial academic or industry technical papers for complex Al system methodology; references to industry guidelines or standards

## Page 10
produced by actuarial standard boards; and any training materials or tutorials that could be helpful for users.

## Page 11
(Links will be added when the final versions of the papers are available)
${ }^{1}$ IAA Paper - Artificial Intelligence Governance Framework
${ }^{2}$ Ibid 14
${ }^{3}$ Ibid 4
${ }^{4}$ Ibid 11
${ }^{5}$ Ibid 10
${ }^{6}$ Ibid 4
${ }^{7}$ Ibid 7
${ }^{8}$ Ibid 12
${ }^{9}$ Ibid 19, 20


