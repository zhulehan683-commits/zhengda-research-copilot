#!/usr/bin/env python3
"""Read-only CSV preflight; counts and diagnostics, never respondent values or inference."""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import Counter
from pathlib import Path

from common import within, sha, read_json, atomic_json, project_root, fail, enable_utf8


def audit(root: Path, data_file: str, schema_file: str, encoding='utf-8-sig') -> dict:
    data_path = within(root, data_file)
    schema_path = within(root, schema_file)
    schema = read_json(schema_path)
    if not isinstance(schema, dict):
        raise ValueError('Schema must be a JSON object')
    schema_fields = {'schema_version', 'description', 'note', 'id_column', 'missing_values', 'variables'}
    if set(schema) - schema_fields:
        raise ValueError('Unsupported schema fields: ' + ', '.join(sorted(set(schema) - schema_fields)))
    variables = schema.get('variables')
    if not isinstance(variables, dict) or not variables:
        raise ValueError('Schema needs a nonempty variables object')
    for name, rule in variables.items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError('Variable names must be nonempty strings')
        if not isinstance(rule, dict):
            raise ValueError('Variable rule must be an object: ' + name)
        allowed_fields = {'type', 'required', 'min', 'max', 'allowed_values', 'description',
                          'label', 'item_group', 'reverse_coding', 'likert_points',
                          'multi_select_separator'}
        if set(rule) - allowed_fields:
            raise ValueError('Unsupported rule fields for ' + name + ': ' + ', '.join(sorted(set(rule) - allowed_fields)))
        kind = rule.get('type')
        if kind not in ('string', 'number', 'integer'):
            raise ValueError('Unsupported variable type: ' + name)
        for bound in ('min', 'max'):
            if bound not in rule:
                continue
            value = rule[bound]
            if value is None:
                raise ValueError('Bounds cannot be null: ' + name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError('Bounds must be finite numbers: ' + name)
            if kind == 'string':
                raise ValueError('String variables do not support min/max: ' + name)
        if rule.get('min') is not None and rule.get('max') is not None and rule['min'] > rule['max']:
            raise ValueError('Reversed bounds: ' + name)
        if 'required' in rule and not isinstance(rule['required'], bool):
            raise ValueError('required must be a boolean: ' + name)
        if 'allowed_values' in rule:
            allowed_values = rule['allowed_values']
            if not isinstance(allowed_values, list) or not allowed_values:
                raise ValueError('allowed_values must be a nonempty array: ' + name)
            if kind == 'string':
                if not all(isinstance(v, str) for v in allowed_values):
                    raise ValueError('allowed_values must contain strings: ' + name)
            else:
                if not all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in allowed_values):
                    raise ValueError('allowed_values must contain numbers: ' + name)
                if kind == 'integer' and not all(isinstance(v, int) and not isinstance(v, bool) for v in allowed_values):
                    raise ValueError('integer allowed_values must contain integers: ' + name)
        if 'item_group' in rule and (not isinstance(rule['item_group'], str)
                                     or not rule['item_group'].strip()):
            raise ValueError('item_group must be a nonempty string: ' + name)
        if 'reverse_coding' in rule:
            if not isinstance(rule['reverse_coding'], bool):
                raise ValueError('reverse_coding must be a boolean: ' + name)
            if rule['reverse_coding']:
                if kind == 'string':
                    raise ValueError('reverse_coding applies to numeric variables only: ' + name)
                if 'likert_points' not in rule and not (
                        rule.get('min') is not None and rule.get('max') is not None):
                    raise ValueError('reverse_coding needs likert_points or explicit min/max: ' + name)
        if 'likert_points' in rule:
            points = rule['likert_points']
            if (isinstance(points, bool) or not isinstance(points, int)
                    or not 2 <= points <= 11):
                raise ValueError('likert_points must be an integer from 2 to 11: ' + name)
            if kind == 'string':
                raise ValueError('likert_points applies to numeric variables only: ' + name)
            if 'allowed_values' in rule or 'min' in rule or 'max' in rule:
                raise ValueError('likert_points expands allowed values; do not combine it with '
                                 'allowed_values/min/max: ' + name)
        if 'multi_select_separator' in rule:
            separator = rule['multi_select_separator']
            if not isinstance(separator, str) or not separator or len(separator) > 3:
                raise ValueError('multi_select_separator must be 1-3 characters: ' + name)
            if kind != 'string':
                raise ValueError('multi_select_separator applies to string variables only: ' + name)
            if 'allowed_values' not in rule:
                raise ValueError('multi_select_separator needs allowed_values: ' + name)
    missing_values = schema.get('missing_values', [''])
    if not isinstance(missing_values, list) or not all(isinstance(v, str) for v in missing_values):
        raise ValueError('missing_values must be an array of strings')
    missing_values = {v.strip() for v in missing_values} | {''}
    id_column = schema.get('id_column')
    if id_column is not None and not isinstance(id_column, str):
        raise ValueError('id_column must be a string')
    if id_column is not None and id_column not in variables:
        raise ValueError('id_column must be a declared variable')
    allowed_by_name = {name: rule['allowed_values'] for name, rule in variables.items()
                       if 'allowed_values' in rule}
    for name, rule in variables.items():
        if 'likert_points' in rule:
            allowed_by_name[name] = list(range(1, rule['likert_points'] + 1))
    item_groups = {}
    for name, rule in variables.items():
        group = rule.get('item_group')
        if group:
            item_groups.setdefault(group.strip(), []).append(name)
    for group, names in item_groups.items():
        if len({variables[n]['type'] for n in names}) != 1:
            raise ValueError('item_group members must share one type: ' + group)
    grouped_names = {name for names in item_groups.values() for name in names}
    stats = {name: {'missing': 0, 'invalid_type': 0, 'out_of_range': 0, 'disallowed': 0, 'valid': 0} for name in variables}
    group_stats = {group: {'columns': names, 'rows_all_missing': 0,
                           'rows_with_multiple_options': 0}
                   for group, names in item_groups.items()}
    rows = Counter()
    identifiers = Counter()
    row_count = malformed = 0
    data_hash = sha(data_path)
    with data_path.open('r', encoding=encoding, newline='') as stream:
        reader = csv.reader(stream)
        header = next(reader, [])
        if not header or any(not v.strip() for v in header) or len(header) != len(set(header)):
            raise ValueError('CSV needs nonempty unique column headers')
        if set(variables) - set(header):
            raise ValueError('CSV is missing schema columns: ' + ', '.join(sorted(set(variables) - set(header))))
        for values in reader:
            row_count += 1
            if len(values) != len(header):
                malformed += 1
                continue
            rows[tuple(values)] += 1
            row = dict(zip(header, values))
            if id_column and row[id_column].strip() not in missing_values:
                identifiers[row[id_column].strip()] += 1
            for group, names in item_groups.items():
                present = [n for n in names if row[n].strip() not in missing_values]
                if not present:
                    group_stats[group]['rows_all_missing'] += 1
                    continue
                selected = 0
                for member in present:
                    raw = row[member].strip()
                    separator = variables[member].get('multi_select_separator')
                    if separator:
                        selected += len([part for part in raw.split(separator)
                                         if part.strip()])
                    elif raw not in {'0', '0.0', 'false', 'False'}:
                        selected += 1
                if selected > 1:
                    group_stats[group]['rows_with_multiple_options'] += 1
            for name, rule in variables.items():
                value = row[name].strip()
                item = stats[name]
                if value in missing_values:
                    item['missing'] += 1
                    continue
                if rule['type'] != 'string':
                    try:
                        numeric = float(value)
                        if not math.isfinite(numeric) or (rule['type'] == 'integer' and not numeric.is_integer()):
                            raise ValueError('Nonfinite or noninteger')
                    except ValueError:
                        item['invalid_type'] += 1
                        continue
                    if numeric < rule.get('min', -math.inf) or numeric > rule.get('max', math.inf):
                        item['out_of_range'] += 1
                        continue
                allowed_values = allowed_by_name.get(name)
                if allowed_values is not None:
                    if rule['type'] == 'string':
                        separator = rule.get('multi_select_separator')
                        if separator:
                            tokens = [part.strip() for part in value.split(separator)]
                            permitted = all(token and token in allowed_values
                                            for token in tokens)
                        else:
                            permitted = value in allowed_values
                    else:
                        permitted = numeric in allowed_values
                    if not permitted:
                        item['disallowed'] += 1
                        continue
                item['valid'] += 1
    if sha(data_path) != data_hash:
        raise ValueError('CSV changed during audit; rerun on a stable snapshot')
    duplicate_ids = sum(n - 1 for n in identifiers.values())
    duplicate_rows = sum(n - 1 for n in rows.values())
    issues = []
    for code, count in [('empty_dataset', int(row_count == 0)), ('malformed_rows', malformed),
                        ('duplicate_id_rows', duplicate_ids)]:
        if count:
            issues.append({'severity': 'block', 'code': code, 'count': count})
    if duplicate_rows:
        issues.append({'severity': 'review', 'code': 'duplicate_rows', 'count': duplicate_rows})
    if set(header) - set(variables):
        issues.append({'severity': 'review', 'code': 'unmapped_columns', 'count': len(set(header) - set(variables))})
    for group, item in group_stats.items():
        required = any(variables[name].get('required') for name in item['columns'])
        if item['rows_all_missing'] and required:
            issues.append({'severity': 'block', 'code': 'group_missing', 'item_group': group,
                           'count': item['rows_all_missing']})
    for name, item in stats.items():
        for code in ('invalid_type', 'out_of_range', 'disallowed', 'missing'):
            if code == 'missing' and name in grouped_names:
                continue
            if item[code]:
                severity = 'review' if code == 'missing' and not variables[name].get('required') else 'block'
                issues.append({'severity': severity, 'variable': name, 'code': code, 'count': item[code]})
        if variables[name].get('reverse_coding') and item['valid']:
            issues.append({'severity': 'review', 'variable': name,
                           'code': 'reverse_coding_declared', 'count': item['valid']})
    return {'status': 'BLOCKED' if any(i['severity'] == 'block' for i in issues) else 'READY_FOR_REVIEW',
            'row_count': row_count, 'column_count': len(header), 'malformed_rows': malformed,
            'duplicate_id_rows': duplicate_ids, 'duplicate_rows': duplicate_rows,
            'dataset_sha256': data_hash, 'schema_sha256': sha(schema_path), 'variables': stats,
            'item_groups': group_stats,
            'unmapped_columns': len(set(header) - set(variables)), 'issues': issues,
            'scientific_validity_verified': False,
            'limitations': ['No automatic row removal or reverse scoring.',
                            'item_group and reverse_coding are reporting declarations only; '
                            'cleaning must be performed and documented separately.',
                            'No proof of respondent identity, consent, representativeness or scale validity.',
                            'Review findings before cleaning or statistical inference.']}


def main() -> int:
    enable_utf8()
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project', required=True)
    p.add_argument('--data', required=True, help='CSV inside project, usually raw_private/')
    p.add_argument('--schema', required=True, help='JSON variable contract inside project')
    p.add_argument('--encoding', default='utf-8-sig')
    p.add_argument('--output', help='Optional project-local JSON diagnostics; never overwrites inputs')
    args = p.parse_args()
    try:
        root = project_root(args.project)
        output = within(root, args.output, must_exist=False) if args.output else None
        if output is not None and output in (within(root, args.data), within(root, args.schema)):
            raise ValueError('Output must differ from data and schema')
        if output is not None:
            if output.relative_to(root).parts[0] != 'analysis':
                raise ValueError('Diagnostics output must be under analysis/')
            if output.exists():
                raise ValueError('Output already exists; choose a new diagnostics filename')
        result = audit(root, args.data, args.schema, args.encoding)
        if output:
            atomic_json(output, result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 3 if result['status'] == 'BLOCKED' else 0
    except (ValueError, OSError, KeyError, TypeError, csv.Error, LookupError) as exc:
        return fail(exc)


if __name__ == '__main__':
    sys.exit(main())
