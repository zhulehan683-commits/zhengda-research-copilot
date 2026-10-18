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

from common import within, sha, read_json, atomic_json, project_root, fail


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
        allowed_fields = {'type', 'required', 'min', 'max', 'allowed_values', 'description', 'label'}
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
    missing_values = schema.get('missing_values', [''])
    if not isinstance(missing_values, list) or not all(isinstance(v, str) for v in missing_values):
        raise ValueError('missing_values must be an array of strings')
    missing_values = {v.strip() for v in missing_values} | {''}
    id_column = schema.get('id_column')
    if id_column is not None and not isinstance(id_column, str):
        raise ValueError('id_column must be a string')
    if id_column is not None and id_column not in variables:
        raise ValueError('id_column must be a declared variable')
    stats = {name: {'missing': 0, 'invalid_type': 0, 'out_of_range': 0, 'disallowed': 0, 'valid': 0} for name in variables}
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
                if 'allowed_values' in rule:
                    allowed_values = rule['allowed_values']
                    if rule['type'] == 'string':
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
    for name, item in stats.items():
        for code in ('invalid_type', 'out_of_range', 'disallowed', 'missing'):
            if item[code]:
                severity = 'review' if code == 'missing' and not variables[name].get('required') else 'block'
                issues.append({'severity': severity, 'variable': name, 'code': code, 'count': item[code]})
    return {'status': 'BLOCKED' if any(i['severity'] == 'block' for i in issues) else 'READY_FOR_REVIEW',
            'row_count': row_count, 'column_count': len(header), 'malformed_rows': malformed,
            'duplicate_id_rows': duplicate_ids, 'duplicate_rows': duplicate_rows,
            'dataset_sha256': data_hash, 'schema_sha256': sha(schema_path), 'variables': stats,
            'unmapped_columns': len(set(header) - set(variables)), 'issues': issues,
            'scientific_validity_verified': False,
            'limitations': ['No automatic row removal or reverse scoring.',
                            'No proof of respondent identity, consent, representativeness or scale validity.',
                            'Review findings before cleaning or statistical inference.']}


def main() -> int:
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
