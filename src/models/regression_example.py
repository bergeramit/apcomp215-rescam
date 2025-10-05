# Import necessary libraries
import numpy as np
from sklearn import datasets
from sklearn.linear_model import LinearRegression

# Load the diabetes dataset
diabetes = datasets.load_diabetes()

# Use only one feature for simplicity
diabetes_X = diabetes.data[:, np.newaxis, 2]

# Split the data into training/testing sets
X_train = diabetes_X[:-20]
X_test = diabetes_X[-20:]

# Split the targets into training/testing sets
y_train = diabetes.target[:-20]
y_test = diabetes.target[-20:]

# Create linear regression object
regr = LinearRegression()

# Train the model using the training sets
regr.fit(X_train, y_train)

# Make predictions using the testing set
y_pred = regr.predict(X_test)

# Print the predictions
print("Predictions:")
print(y_pred)
