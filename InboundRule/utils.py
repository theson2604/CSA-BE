import json
import pandas as pd

from app.common.errors import HTTPBadRequest


async def read_file(file):
    file_extension = file.filename.split(".")[-1]
    if file_extension.lower() == "csv":
        df = pd.read_csv(file.file, keep_default_na=False)
    elif file_extension.lower() == "json":
        default = 'lines'
        file.file.seek(0)
        first_char = await file.read(1)
        file.file.seek(0)
        if first_char == b'[':
            default = 'array'

        if default == 'lines':
            df = pd.read_json(file.file, lines=True)
        else:
            print(file.file, type(file.file))
            data = json.load(file.file)
            df = pd.DataFrame(data)
    else:
        raise HTTPBadRequest(f"Invalid file type {file_extension}.")

    return df