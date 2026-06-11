# Amazon SageMaker Deployment

This document describes how to deploy the two trained scikit-learn models —
the **Random Forest Regressor** (California Housing) and the
**Logistic Regression Classifier** (Bank Marketing) — to live SageMaker
real-time inference endpoints.

## 1. Prerequisites

- AWS account with permissions for SageMaker, S3, and IAM
- An IAM role with the `AmazonSageMakerFullAccess` policy (or a scoped
  equivalent), referenced as `SAGEMAKER_ROLE_ARN` in `.env`
- AWS credentials configured locally (`aws configure` or environment
  variables `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`)
- Trained model artifacts present in `models/`:
  - `models/random_forest_regressor.pkl`
  - `models/logistic_regression_classifier.pkl`

## 2. Package the model artifacts

SageMaker's SKLearn container expects a `model.tar.gz` containing the model
file plus the inference entrypoint script. From the project root:

```bash
# Regression
mkdir -p build/regression
cp models/random_forest_regressor.pkl build/regression/
cp inference/regression_sagemaker_entry.py build/regression/
tar -czf regression-model.tar.gz -C build/regression .

# Classification
mkdir -p build/classification
cp models/logistic_regression_classifier.pkl build/classification/
cp inference/classification_sagemaker_entry.py build/classification/
tar -czf classification-model.tar.gz -C build/classification .
```

## 3. Upload artifacts to S3

```bash
aws s3 cp regression-model.tar.gz s3://<your-bucket>/models/regression-model.tar.gz
aws s3 cp classification-model.tar.gz s3://<your-bucket>/models/classification-model.tar.gz
```

## 4. Deploy with the SageMaker Python SDK

```python
import sagemaker
from sagemaker.sklearn.model import SKLearnModel

role = "<SAGEMAKER_ROLE_ARN>"

# Regression endpoint
reg_model = SKLearnModel(
    model_data="s3://<your-bucket>/models/regression-model.tar.gz",
    role=role,
    entry_point="regression_sagemaker_entry.py",
    framework_version="1.2-1",
)
reg_predictor = reg_model.deploy(
    initial_instance_count=1,
    instance_type="ml.m5.large",
    endpoint_name="housing-rf-regressor",
)

# Classification endpoint
cls_model = SKLearnModel(
    model_data="s3://<your-bucket>/models/classification-model.tar.gz",
    role=role,
    entry_point="classification_sagemaker_entry.py",
    framework_version="1.2-1",
)
cls_predictor = cls_model.deploy(
    initial_instance_count=1,
    instance_type="ml.m5.large",
    endpoint_name="bank-marketing-classifier",
)
```

## 5. Configure the application

Set the endpoint names in `.env`:

```
REGRESSION_ENDPOINT_NAME=housing-rf-regressor
CLASSIFICATION_ENDPOINT_NAME=bank-marketing-classifier
```

In the Streamlit app, toggle **SageMaker Endpoints** on in the sidebar.
`app/sagemaker_client.py` will invoke these endpoints via
`sagemaker-runtime.invoke_endpoint`. If the endpoints are unreachable, the
app automatically falls back to the local model artifacts in `models/`
(`inference/regression_inference.py` and `inference/classification_inference.py`).

## 6. Test the endpoints

```bash
aws sagemaker-runtime invoke-endpoint \
  --endpoint-name housing-rf-regressor \
  --body '{"instances": [[8.3252, 41.0, 6.984, 1.023, 322.0, 2.556, 37.88, -122.23]]}' \
  --content-type application/json \
  output.json && cat output.json
```

## 7. Clean up

To avoid ongoing charges, delete the endpoints when finished:

```bash
aws sagemaker delete-endpoint --endpoint-name housing-rf-regressor
aws sagemaker delete-endpoint --endpoint-name bank-marketing-classifier
```
