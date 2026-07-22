from pathlib import Path
import csv
import re
import sqlite3
import sys

import pandas as pd


# Pasta onde estão os arquivos CSV
DATABASE_FOLDER = Path(__file__).resolve().parent

# Nome do banco SQLite que será criado
SQLITE_FILE = DATABASE_FOLDER / "ravenstack.db"


def normalize_table_name(filename: str) -> str:
    """
    Converte o nome do arquivo CSV em um nome de tabela válido.

    Exemplo:
    ravenstack_accounts.csv -> accounts
    ravenstack_feature_usage.csv -> feature_usage
    """

    table_name = Path(filename).stem.lower()

    # Remove o prefixo ravenstack_
    table_name = re.sub(r"^ravenstack_", "", table_name)

    # Substitui caracteres inválidos por _
    table_name = re.sub(r"[^a-z0-9_]+", "_", table_name)

    # Remove _ no início ou no final
    table_name = table_name.strip("_")

    # Evita tabela começando com número
    if table_name and table_name[0].isdigit():
        table_name = f"table_{table_name}"

    return table_name


def detect_encoding(csv_path: Path) -> str:
    """
    Tenta identificar uma codificação válida para o arquivo CSV.
    """

    encodings = [
        "utf-8-sig",
        "utf-8",
        "latin-1",
        "cp1252",
    ]

    for encoding in encodings:
        try:
            with csv_path.open("r", encoding=encoding) as file:
                file.read(10000)

            return encoding
        except UnicodeDecodeError:
            continue

    raise UnicodeDecodeError(
        "unknown",
        b"",
        0,
        1,
        f"Não foi possível identificar a codificação de {csv_path.name}",
    )


def detect_separator(csv_path: Path, encoding: str) -> str:
    """
    Identifica o separador utilizado no CSV.
    Tenta reconhecer vírgula, ponto e vírgula, tabulação ou pipe.
    """

    with csv_path.open("r", encoding=encoding, newline="") as file:
        sample = file.read(10000)

    try:
        dialect = csv.Sniffer().sniff(
            sample,
            delimiters=[",", ";", "\t", "|"],
        )
        return dialect.delimiter
    except csv.Error:
        return ","


def normalize_column_names(dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Padroniza os nomes das colunas para facilitar consultas SQL.

    Exemplo:
    Account ID -> account_id
    Monthly Revenue -> monthly_revenue
    """

    normalized_columns = []
    existing_columns = set()

    for column in dataframe.columns:
        normalized = str(column).strip().lower()
        normalized = re.sub(r"[^a-z0-9_]+", "_", normalized)
        normalized = re.sub(r"_+", "_", normalized)
        normalized = normalized.strip("_")

        if not normalized:
            normalized = "column"

        original_normalized = normalized
        counter = 2

        # Evita colunas duplicadas
        while normalized in existing_columns:
            normalized = f"{original_normalized}_{counter}"
            counter += 1

        existing_columns.add(normalized)
        normalized_columns.append(normalized)

    dataframe.columns = normalized_columns
    return dataframe


def read_csv_file(csv_path: Path) -> pd.DataFrame:
    """
    Lê o CSV tentando preservar corretamente os dados.
    """

    encoding = detect_encoding(csv_path)
    separator = detect_separator(csv_path, encoding)

    print(f"  Codificação: {encoding}")
    print(f"  Separador: {repr(separator)}")

    try:
        dataframe = pd.read_csv(
            csv_path,
            encoding=encoding,
            sep=separator,
            low_memory=False,
        )
    except Exception as error:
        raise RuntimeError(
            f"Erro ao ler o arquivo {csv_path.name}: {error}"
        ) from error

    dataframe = normalize_column_names(dataframe)

    return dataframe


def import_csv_files() -> None:
    """
    Importa todos os arquivos CSV da pasta para um único SQLite.
    """

    if not DATABASE_FOLDER.exists():
        raise FileNotFoundError(
            f"A pasta não foi encontrada:\n{DATABASE_FOLDER}"
        )

    csv_files = sorted(DATABASE_FOLDER.glob("*.csv"))

    if not csv_files:
        print("Nenhum arquivo CSV foi encontrado na pasta:")
        print(DATABASE_FOLDER)
        return

    print(f"Pasta de origem: {DATABASE_FOLDER}")
    print(f"Banco SQLite: {SQLITE_FILE}")
    print(f"Arquivos CSV encontrados: {len(csv_files)}")
    print("-" * 70)

    with sqlite3.connect(SQLITE_FILE) as connection:
        connection.execute("PRAGMA foreign_keys = ON;")

        imported_tables = []

        for csv_path in csv_files:
            table_name = normalize_table_name(csv_path.name)

            print(f"\nImportando: {csv_path.name}")
            print(f"Tabela: {table_name}")

            dataframe = read_csv_file(csv_path)

            dataframe.to_sql(
                name=table_name,
                con=connection,
                if_exists="replace",
                index=False,
                chunksize=1000,
            )

            row_count = len(dataframe)
            column_count = len(dataframe.columns)

            print(
                f"  Importação concluída: "
                f"{row_count:,} linhas e {column_count} colunas"
            )

            imported_tables.append(
                {
                    "file": csv_path.name,
                    "table": table_name,
                    "rows": row_count,
                    "columns": column_count,
                }
            )

        connection.commit()

    print("\n" + "=" * 70)
    print("BANCO SQLITE CRIADO COM SUCESSO")
    print("=" * 70)

    for item in imported_tables:
        print(
            f"{item['file']} -> {item['table']} "
            f"({item['rows']:,} linhas)"
        )

    print(f"\nArquivo criado em:\n{SQLITE_FILE}")


if __name__ == "__main__":
    try:
        import_csv_files()
    except Exception as error:
        print("\nOcorreu um erro durante a importação:")
        print(error)
        sys.exit(1)
