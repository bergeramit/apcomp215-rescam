import dataloader
from abc import ABC, abstractmethod

class Preprocess(ABC):
    @abstractmethod
    def clean(self):
        pass

class PreprocessCEAS08(Preprocess):
    def __init__(self, full_path):
        self.full_path = full_path

    def clean(self):
        pass

def main():
    files = dataloader.get_raw_files_local()
    print(files)


if __name__ == "__main__":
    main()