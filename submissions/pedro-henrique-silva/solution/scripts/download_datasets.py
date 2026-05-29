"""Baixa datasets do desafio usando kagglehub.

Uso:
  python scripts/download_datasets.py
"""

import kagglehub


def main() -> None:
    dataset_1 = kagglehub.dataset_download("suraj520/customer-support-ticket-dataset")
    dataset_2 = kagglehub.dataset_download("adisongoh/it-service-ticket-classification-dataset")

    print("Dataset 1 path:", dataset_1)
    print("Dataset 2 path:", dataset_2)


if __name__ == "__main__":
    main()
