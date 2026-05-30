import pandas as pd
import json
import os
import unicodedata


# def process_workflow_objects_tasks(input_path, output_path):
#     # --- Load line-delimited JSON objects from file ---
#     with open(input_path, "r", encoding='utf-8') as file:
#         rows = [json.loads(line) for line in file if line.strip()]
#     df = pd.DataFrame(rows)
#
#     # Debug: Check how the data is loaded
#     # print(f"Loaded data from {input_path}:")
#     # print(df.head())  # Print first few rows of the DataFrame for inspection
#
#     # --- Drop unnecessary columns ---
#     columns_to_drop = [
#         "kind", "schema", "hash", "triggers", "events",
#         "actions", "confirmed_by", "for_each", "rework_upon"
#     ]
#     df.drop(columns=[col for col in columns_to_drop if col in df.columns], errors='ignore', inplace=True)
#
#     # Debug: Check DataFrame after dropping columns
#     # print("After dropping unnecessary columns:")
#     # print(df.head())
#
#     # --- Parse 'attachments' field safely ---
#     def parse_attachments(val):
#         if isinstance(val, str):
#             try:
#                 return json.loads(val)
#             except json.JSONDecodeError:
#                 return []
#         return val if isinstance(val, list) else []
#
#     df['parsed_attachments'] = df['attachments'].apply(parse_attachments)
#
#     # Debug: Check parsed attachments
#     # print("Parsed attachments (sample):")
#     # print(df['parsed_attachments'].head())
#
#     # --- Extract URLs and Titles from attachments ---
#     def extract_urls_titles(attachments):
#         urls, titles = [], []
#         for item in attachments:
#             if isinstance(item, dict):
#                 urls.append(item.get('url', ''))
#                 titles.append(item.get('title', ''))
#         return urls, titles
#
#     df['urls'], df['titles'] = zip(*df['parsed_attachments'].apply(extract_urls_titles))
#
#     # Debug: Check extracted URLs and Titles
#     # print("Extracted URLs and Titles (sample):")
#     # print(df[['urls', 'titles']].head())
#
#     # --- Dynamically expand into Url-{i} and Title-{i} columns ---
#     max_len = df['urls'].apply(len).max()
#
#     for i in range(max_len):
#         df[f'Url-{i + 1}'] = df['urls'].apply(lambda x: x[i] if i < len(x) else '')
#         df[f'Title-{i + 1}'] = df['titles'].apply(lambda x: x[i] if i < len(x) else '')
#
#     #df = df[~((df['Url-1'] == '') & (df['Title-1'] == ''))]
#
#     # # Debug: Check dynamic columns for URLs and Titles
#     # print("Dynamic columns for URLs and Titles (sample):")
#     # print(df[[f'Url-{i + 1}' for i in range(max_len)] + [f'Title-{i + 1}' for i in range(max_len)]].head())
#
#     # --- Final cleanup ---
#     df.drop(columns=['parsed_attachments', 'urls', 'titles'], inplace=True)
#     df.drop_duplicates(subset=['name', 'id', 'Url-1', 'Title-1', 'Url-2', 'Title-2', 'Url-3', 'Title-3',
# 'Url-4', 'Title-4', 'Url-5', 'Title-5', 'Url-6', 'Title-6', 'Url-7',
# 'Title-7', 'Url-8', 'Title-8', 'Url-9', 'Title-9', 'Url-10', 'Title-10',
# 'Url-11', 'Title-11', 'Url-12', 'Title-12', 'Url-13', 'Title-13',
# 'Url-14', 'Title-14', 'Url-15', 'Title-15', 'Url-16', 'Title-16',
# 'Url-17', 'Title-17'], inplace=True)
#     df.fillna('NA', inplace=True)
#     df['Index'] = range(1, len(df) + 1)
#
#     # --- Export to Excel ---
#     df.to_excel(output_path, index=False)
#
#     # # Debug: Check the final DataFrame before saving
#     # print(f"Final Data (sample):")
#     # print(df.head())
#
#     # Optional: print selected columns for confirmation
#     # selected_cols = ['id'] + [col for col in df.columns if col.startswith('Url-') or col.startswith('Title-')]
#     # print(f"Selected Columns:")
#     # print(df[selected_cols].head())

def process_work_objects_takts(input_path, output_path):
    # --- Load line-delimited JSON objects from file ---
    with open(input_path, "r", encoding='utf-8') as file:
        rows = [json.loads(line) for line in file if line.strip()]
    df = pd.DataFrame(rows)

    # --- Clean 'description' and filter rows ending with '~' ---
    def clean_text(val):
        if pd.isnull(val):
            return ''
        return unicodedata.normalize('NFKC', str(val)).replace('\xa0', ' ').strip()

    if 'description' in df.columns:
        df['description_cleaned'] = df['description'].apply(clean_text)
        df1 = df[df['description_cleaned'].str.endswith('~')].copy()
    else:
        df1 = pd.DataFrame()  # Empty DataFrame fallback

    if df1.empty:
        print("No rows with 'description' ending with '~' were found.")
        return

    # --- Drop unnecessary columns ---
    columns_to_drop = [
        'hash', 'kind', 'schema', 'description', 'description_cleaned', 'attachments',
        'triggers', 'events', 'sap_operation', 'goods_in',
        'limitted_to', 'for_each_unit_of', 'rework_upon'
    ]
    df1.drop(columns=[col for col in columns_to_drop if col in df1.columns], inplace=True)

    # --- Rename columns ---
    rename_dict = {
        'id': 'sub_id',
        'name': 'Takt Name',
        'workitem_order': 'id'
    }
    df1.rename(columns=rename_dict, inplace=True)

    # --- Prepare the expanded rows ---
    expanded_rows = []
    for _, row in df1.iterrows():
        sub_id = row['sub_id']
        takt_name = row['Takt Name']
        ids_raw = row['id']

        if isinstance(ids_raw, list):
            ids = [str(x).strip() for x in ids_raw]
        elif isinstance(ids_raw, str):
            ids = [x.strip() for x in ids_raw.strip('{}').split(',')]
        else:
            ids = []

        for single_id in ids:
            expanded_rows.append({
                'sub_id': sub_id,
                'Takt Name': takt_name,
                'id': single_id
            })

    # --- Create the final DataFrame ---
    df1 = pd.DataFrame(expanded_rows, columns=['sub_id', 'Takt Name', 'id'])

    # --- Clean and convert 'id' ---
    def clean_and_convert_id(val):
        if pd.isnull(val):
            return None
        val_str = str(val).replace('[', '').replace(']', '').strip()
        if val_str == '':
            return None
        try:
            return int(val_str)
        except ValueError:
            return None

    df1.columns = [col.strip() for col in df1.columns]
    df1['id'] = df1['id'].apply(clean_and_convert_id)
    df1['Index'] = range(1, len(df1) + 1)
    df1 = df1[~df1.duplicated(subset=['sub_id', 'Takt Name', 'id'], keep='first')]

    # Fill missing 'id' with 0
    df1['id'] = df1['id'].fillna(0).astype(int)

    # --- Export to Excel ---
    df1.to_excel(output_path, index=False)

def process_shop_floors(input_path, output_path):
    # --- Load line-delimited JSON objects from file ---
    with open(input_path, "r", encoding='utf-8') as file:
        rows = [json.loads(line) for line in file if line.strip()]
    df = pd.DataFrame(rows)

    # --- Drop unnecessary columns ---
    df.drop(columns=[
        'description', 'organization', 'modified', 'deleted', 'correlation_id',
        'daily_task', 'layout', 'owner', 'commands'
    ], inplace=True)

    # --- Rename columns ---
    rename_dict = {
        'id': 'id',
        'name': 'Shop_Name',
        'takt_order': 'sub_id'
    }
    df.rename(columns=rename_dict, inplace=True)

    # --- Prepare the expanded rows ---
    expanded_rows = []
    for _, row in df.iterrows():
        id = row['id']
        shop_name = row['Shop_Name']
        ids_raw = row['sub_id']

        if isinstance(ids_raw, list):
            ids = [str(x).strip() for x in ids_raw]
        elif isinstance(ids_raw, str):
            ids = [x.strip() for x in ids_raw.strip('{}').split(',')]
        else:
            ids = []

        for single_id in ids:
            expanded_rows.append({
                'id': id,
                'Shop_Name': shop_name,
                'sub_id': single_id
            })

    # Create the final DataFrame
    df = pd.DataFrame(expanded_rows, columns=['id', 'Shop_Name', 'sub_id'])

    # --- Clean and convert 'id' ---
    def clean_and_convert_id(val):
        if pd.isnull(val):
            return None
        val_str = str(val).replace('[','').replace(']','').strip()
        if val_str == '':
            return None
        try:
            return int(val_str)
        except ValueError:
            return None  # or raise an error/log it depending on your use case

    df.columns = [col.strip() for col in df.columns]
    df['sub_id'] = df['sub_id'].apply(clean_and_convert_id)
    df['Index'] = range(1, len(df) + 1)
    df = df[~df.duplicated(subset=['id', 'Shop_Name', 'sub_id'], keep='first')]

    # Fill missing 'id' with 0
    df['id'] = df['id'].fillna(0).astype(int)

    # --- Export to Excel ---
    df.to_excel(output_path, index=False)

def process_workflow_groups(input_path, output_path):
    # --- Load line-delimited JSON objects from file ---
    with open(input_path, "r", encoding='utf-8') as file:
        rows = [json.loads(line) for line in file if line.strip()]
    df = pd.DataFrame(rows)

    # --- Rename columns ---
    rename_dict = {
        'workflow': 'system_type',
        'group': 'group',
        'shop_floor': 'shop_number'
    }
    df.rename(columns=rename_dict, inplace=True)

    system_type_map = {
        1: "GeminiSEM & Crossbeam",
        2: "Crossbeam Integration",
        3: "Sigma",
        7: "EVO"
    }

    df['system_type'] = df['system_type'].map(system_type_map).fillna(df['system_type'])
    df['Index'] = range(1, len(df) + 1)

    # --- Export to Excel ---
    df.to_excel(output_path, index=False)

# def process_workflow_objects_tasks_2(input_path, output_path):
#     # --- Load line-delimited JSON objects from file ---
#     with open(input_path, "r", encoding='utf-8') as file:
#         rows = [json.loads(line) for line in file if line.strip()]
#     df = pd.DataFrame(rows)
#
#     # --- Drop unnecessary columns ---
#     columns_to_drop = [
#         "kind", "schema", "hash", "triggers", "events",
#         "attachments", "confirmed_by", "for_each", "rework_upon"
#     ]
#     df = df.drop(columns=[col for col in columns_to_drop if col in df.columns], errors='ignore')
#
#     # --- Parse the 'actions' field and explode text ---
#
#     # Handle cases where 'actions' may be a JSON string or a list
#     def parse_actions(val):
#         if isinstance(val, str):
#             try:
#                 return json.loads(val)
#             except Exception:
#                 return []
#         elif isinstance(val, list):
#             return val
#         return []
#
#     df['parsed_actions'] = df['actions'].apply(parse_actions)
#
#     # --- Create rows for each text in 'actions' array ---
#     # Each row will contain [id, name, action_text]
#     rows_expanded = []
#     for _, row in df.iterrows():
#         id_, name = row.get('id'), row.get('name')
#         actions = row['parsed_actions']
#         if not isinstance(actions, list):
#             continue
#         for action in actions:
#             if isinstance(action, dict) and 'text' in action:
#                 rows_expanded.append({
#                     'id': id_,
#                     'name': name,
#                     'actions': action['text']
#                 })
#
#     # Create DataFrame from the expanded rows
#     df_out = pd.DataFrame(rows_expanded, columns=['id', 'name', 'actions'])
#
#     # Fill missing 'id' with 'NA'
#     df_out['id'] = df_out['id'].fillna('NA')
#     df_out['name'] = df_out['name'].fillna('')
#     df_out['actions'] = df_out['actions'].fillna('')
#
#     # Add index column if desired (optional)
#     df_out['Index'] = range(1, len(df_out) + 1)
#
#     # Export to Excel
#     df_out.to_excel(output_path, index=False)

def process_workflow_objects_tasks_combined(input_path, attachment_output, actions_output):
    # --- Load line-delimited JSON objects from input file once ---
    with open(input_path, "r", encoding='utf-8') as file:
        rows = [json.loads(line) for line in file if line.strip()]
    df_src = pd.DataFrame(rows)

    # --- Process Attachments ---
    df_attachments = df_src.copy()
    columns_to_drop_attachments = [
        "kind", "schema", "hash", "triggers", "events",
        "actions", "confirmed_by", "for_each", "rework_upon"
    ]
    df_attachments = df_attachments.drop(
        columns=[col for col in columns_to_drop_attachments if col in df_attachments.columns],
        errors='ignore'
    )

    if 'description' in df_attachments.columns:
        df_attachments = df_attachments[df_attachments['description'].astype(str).str.strip().str.endswith('~')]

    def parse_attachments(val):
        if isinstance(val, str):
            try:
                return json.loads(val)
            except Exception:
                return []
        return val if isinstance(val, list) else []

    if 'attachments' in df_attachments.columns:
        df_attachments['parsed_attachments'] = df_attachments['attachments'].apply(parse_attachments)

        def extract_urls_titles(attachments):
            urls, titles = [], []
            for item in attachments:
                if isinstance(item, dict):
                    urls.append(item.get('url', ''))
                    titles.append(item.get('title', ''))
            return urls, titles

        df_attachments['urls'], df_attachments['titles'] = zip(*df_attachments['parsed_attachments'].apply(extract_urls_titles))

        max_len = df_attachments['urls'].apply(len).max() if len(df_attachments['urls']) > 0 else 0
        for i in range(max_len):
            df_attachments[f'Url-{i+1}'] = df_attachments['urls'].apply(lambda x: x[i] if i < len(x) else '')
            df_attachments[f'Title-{i+1}'] = df_attachments['titles'].apply(lambda x: x[i] if i < len(x) else '')

        df_attachments.drop(columns=['parsed_attachments', 'urls', 'titles'], inplace=True)

        # Deduplicate on only hashable columns
        url_cols = [f'Url-{i+1}' for i in range(max_len)]
        title_cols = [f'Title-{i+1}' for i in range(max_len)]
        subset_cols = ['name', 'id'] + url_cols + title_cols
        subset_cols = [c for c in subset_cols if c in df_attachments.columns]
        df_attachments.drop_duplicates(subset=subset_cols, inplace=True)

        df_attachments.fillna('NA', inplace=True)
        df_attachments['Index'] = range(1, len(df_attachments) + 1)
        df_attachments.to_excel(attachment_output, index=False)
    else:
        pd.DataFrame({'error': ['no attachments column found']}).to_excel(attachment_output, index=False)

    # --- Process Actions ---
    df_actions = df_src.copy()
    columns_to_drop_actions = [
        "kind", "schema", "hash", "triggers", "events",
        "attachments", "confirmed_by", "for_each", "rework_upon"
    ]
    df_actions = df_actions.drop(
        columns=[col for col in columns_to_drop_actions if col in df_actions.columns],
        errors='ignore'
    )

    if 'description' in df_actions.columns:
        df_actions = df_actions[df_actions['description'].astype(str).str.strip().str.endswith('~')]

    def parse_actions(val):
        if isinstance(val, str):
            try:
                return json.loads(val)
            except Exception:
                return []
        elif isinstance(val, list):
            return val
        return []

    if 'actions' in df_actions.columns:
        df_actions['parsed_actions'] = df_actions['actions'].apply(parse_actions)
        rows_expanded = []
        for _, row in df_actions.iterrows():
            id_, name = row.get('id'), row.get('name')
            actions = row['parsed_actions']
            if not isinstance(actions, list):
                continue
            for action in actions:
                if isinstance(action, dict) and 'text' in action:
                    rows_expanded.append({'id': id_, 'name': name, 'actions': action['text']})
        df_actions_out = pd.DataFrame(rows_expanded, columns=['id', 'name', 'actions'])
        df_actions_out['id'] = df_actions_out['id'].fillna('NA')
        df_actions_out['name'] = df_actions_out['name'].fillna('')
        df_actions_out['actions'] = df_actions_out['actions'].fillna('')
        df_actions_out['Index'] = range(1, len(df_actions_out) + 1)
        df_actions_out.to_excel(actions_output, index=False)
    else:
        pd.DataFrame({'error': ['no actions column found']}).to_excel(actions_output, index=False)

# Update your mapping to include a lambda for argument unpacking for multi-output functions:
CLEANING_FUNCTIONS = {
    "erp_workflows_objects_task": process_workflow_objects_tasks_combined,
    "erp_workflows_objects_takt": process_work_objects_takts,
    "staging_shop_floors": process_shop_floors,
    "staging_workflow_groups": process_workflow_groups
}

def process_directory(bad_data_dir, good_data_dir, logger=None):
    os.makedirs(good_data_dir, exist_ok=True)
    for filename in os.listdir(bad_data_dir):
        if filename.endswith('.json'):
            base = os.path.splitext(filename)[0]
            input_path = os.path.join(bad_data_dir, filename)

            if base in CLEANING_FUNCTIONS:
                if base == "erp_workflows_objects_task":
                    # Two outputs: _1.xlsx (attachments), _2.xlsx (actions)
                    output_path_attachments = os.path.join(good_data_dir, base + "_1.xlsx")
                    output_path_actions = os.path.join(good_data_dir, base + "_2.xlsx")
                    if logger:
                        logger.info(f"Processing {filename}: {output_path_attachments} and {output_path_actions}")
                    else:
                        print(f"Processing {filename}: {output_path_attachments} and {output_path_actions}")
                    CLEANING_FUNCTIONS[base](input_path, output_path_attachments, output_path_actions)
                else:
                    output_path = os.path.join(good_data_dir, base + ".xlsx")
                    if logger:
                        logger.info(f"Processing {filename}: {output_path}")
                    else:
                        print(f"Processing {filename}: {output_path}")
                    CLEANING_FUNCTIONS[base](input_path, output_path)
            else:
                msg = f"No cleaning function for {filename}, skipping."
                if logger:
                    logger.warning(msg)
                else:
                    print(msg)
