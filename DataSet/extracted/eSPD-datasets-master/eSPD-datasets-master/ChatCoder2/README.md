# CC2 preprocessor

Usage:
```
python handle_data.py <some_indicator>
```

This generates
`processed_data/ChatCoder2-segments_<some_indicator>.tsv` and
`processed_data/ChatCoder2-datapack-<some_indicator>.json`.

The TSV file is used for model training together with a PAN12 TSV file (as PANC). The pickle is used for evaluation as it is easier to work with. The text content of messages in the pickle and TSV files is the same.
