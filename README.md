# Rescam App
## Cleaning and setting up the datapipeline+RAG
```
# Build/Run the docker (cd ./src/datapipeline)
./docket-shell.sh

# Access Docker Shell
docker run -it --rm preprocess-app


# In the container
# Clean dataset
python preprocess_clean.py

# NOTE: this can take a log time to index and create the rag - careful runninmg this
python preprocess_rag.py

```

## Running the scan
```
# Build/Run the docker (cd ./src/models)
./docket-shell.sh

# Access Docker Shell
docker run -it --rm regression-app

# In the container -> all default values are targeted to match Rescam
python model_rag.py
```
