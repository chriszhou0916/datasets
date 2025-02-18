# coding=utf-8
# Copyright 2019 The TensorFlow Datasets Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Script to document datasets.

python -m tensorflow_datasets.scripts.document_datasets

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import cgi
import collections
import os
import sys

from absl import app
import tensorflow as tf
import tensorflow_datasets as tfds
from tensorflow_datasets.core.utils import py_utils

BASE_URL = "https://github.com/tensorflow/datasets/tree/master/tensorflow_datasets"

INTERNAL_DOC = """\
"""

# ImageLabelFolder require an extra constructor arg so is handled separately
# WmtTranslate: The raw wmt can only be instantiated with the config kwargs
# TODO(tfds): Document the manual_dir datasets in a separate section
BUILDER_BLACKLIST = ["image_label_folder", "wmt_translate"]

DOC = """\
<!-- This file is automatically generated by tfds.scripts.document_datasets and
all modifications will be erased, please edit the original document_datasets.py
file. -->
# Datasets

Note: The datasets documented here are from `HEAD` and so not all are available
in the current `tensorflow-datasets` package. They are all accessible in our
nightly package `tfds-nightly`.

---

## Usage

```python
# See all registered datasets
tfds.list_builders()

# Load a given dataset by name, along with the DatasetInfo
data, info = tfds.load("mnist", with_info=True)
train_data, test_data = data['train'], data['test']
assert isinstance(train_data, tf.data.Dataset)
assert info.features['label'].num_classes == 10
assert info.splits['train'].num_examples == 60000

# You can also access a builder directly
builder = tfds.builder("mnist")
assert builder.info.splits['train'].num_examples == 60000
builder.download_and_prepare()
datasets = builder.as_dataset()

# If you need NumPy arrays
np_datasets = tfds.as_numpy(datasets)
```
## All Datasets

{toc}

---
"""

SECTION_DATASETS = """\
## [`{section_name}`](#{section_name})

{datasets}
"""

CONFIG_BULLET = """\
* `{name}` (`v{version}`) (`Size: {size}`): {description}
"""

SINGLE_CONFIG_ENTRY = """\
## `{builder_name}/{config_name}`

{feature_information}

"""

DATASET_WITH_CONFIGS_ENTRY = """\
# `{snakecase_name}`

{description_prefix}{description}

* URL: [{url}]({url})
* `DatasetBuilder`: [`{module_and_class}`]({cls_url})

`{snakecase_name}` is configured with `{config_cls}` and has the following
configurations predefined (defaults to the first one):

{config_names}

{configs}

## Statistics
{statistics_information}

## Urls
{urls}

## Supervised keys (for `as_supervised=True`)
`{supervised_keys}`

{citation}
---
"""

DATASET_ENTRY = """\
# `{snakecase_name}`

{description_prefix}{description}

* URL: [{url}]({url})
* `DatasetBuilder`: [`{module_and_class}`]({cls_url})
* Version: `v{version}`
* Size: `{size}`

## Features
{feature_information}

## Statistics
{statistics_information}

## Urls
{urls}

## Supervised keys (for `as_supervised=True`)
`{supervised_keys}`

{citation}
---
"""

FEATURE_BLOCK = """\
```python
%s
```
"""

CITATION_BLOCK = """\
## Citation
```
%s
```
"""

STATISTICS_TABLE = """\
Split  | Examples
:----- | ---:
{split_statistics}
"""


def cls_url(module_name):
  mod_file = sys.modules[module_name].__file__
  if mod_file.endswith("pyc"):
    mod_file = mod_file[:-1]
  path = os.path.relpath(mod_file, py_utils.tfds_dir())
  return os.path.join(BASE_URL, path)


def tfds_mod_name(mod_name):
  parts = mod_name.split(".")
  return ".".join(["tfds"] + parts[1:])


def url_from_info(info):
  return (info.urls and info.urls[0]) or "https://www.tensorflow.org/datasets"


def format_urls(urls):
  return "\n".join([" * [{url}]({url})".format(url=url) for url in urls])


def document_single_builder(builder):
  """Doc string for a single builder, with or without configs."""
  mod_name = builder.__class__.__module__
  cls_name = builder.__class__.__name__
  mod_file = sys.modules[mod_name].__file__
  if mod_file.endswith("pyc"):
    mod_file = mod_file[:-1]

  description_prefix = ""


  if builder.builder_configs:
    # Dataset with configs; document each one
    config_docs = []
    for config in builder.BUILDER_CONFIGS:
      builder = tfds.builder(builder.name, config=config)
      info = builder.info
      # TODO(rsepassi): document the actual config object
      config_doc = SINGLE_CONFIG_ENTRY.format(
          builder_name=builder.name,
          config_name=config.name,
          description=config.description,
          version=config.version,
          feature_information=make_feature_information(info),
          size=tfds.units.size_str(info.size_in_bytes),
      )
      config_docs.append(config_doc)
    out_str = DATASET_WITH_CONFIGS_ENTRY.format(
        snakecase_name=builder.name,
        module_and_class="%s.%s" % (tfds_mod_name(mod_name), cls_name),
        cls_url=cls_url(mod_name),
        config_names="\n".join([
            CONFIG_BULLET.format(name=config.name,
                                 description=config.description,
                                 version=config.version,
                                 size=tfds.units.size_str(tfds.builder(
                                     builder.name, config=config)
                                                          .info.size_in_bytes))
            for config in builder.BUILDER_CONFIGS]),
        config_cls="%s.%s" % (tfds_mod_name(mod_name),
                              type(builder.builder_config).__name__),
        configs="\n".join(config_docs),
        urls=format_urls(info.urls),
        url=url_from_info(info),
        supervised_keys=str(info.supervised_keys),
        citation=make_citation(info.citation),
        statistics_information=make_statistics_information(info),
        description=builder.info.description,
        description_prefix=description_prefix,
    )
  else:
    info = builder.info
    out_str = DATASET_ENTRY.format(
        snakecase_name=builder.name,
        module_and_class="%s.%s" % (tfds_mod_name(mod_name), cls_name),
        cls_url=cls_url(mod_name),
        description=info.description,
        description_prefix=description_prefix,
        version=info.version,
        feature_information=make_feature_information(info),
        statistics_information=make_statistics_information(info),
        urls=format_urls(info.urls),
        url=url_from_info(info),
        supervised_keys=str(info.supervised_keys),
        citation=make_citation(info.citation),
        size=tfds.units.size_str(info.size_in_bytes),
    )

  out_str = schema_org(builder) + "\n" + out_str
  return out_str


def make_module_to_builder_dict(datasets=None):
  """Get all builders organized by module in nested dicts."""
  # pylint: disable=g-long-lambda
  # dict to hold tfds->image->mnist->[builders]
  module_to_builder = collections.defaultdict(
      lambda: collections.defaultdict(
          lambda: collections.defaultdict(list)))
  # pylint: enable=g-long-lambda

  if datasets:
    builders = [tfds.builder(name) for name in datasets]
  else:
    builders = [
        tfds.builder(name)
        for name in tfds.list_builders()
        if name not in BUILDER_BLACKLIST
    ] + [tfds.builder("image_label_folder", dataset_name="image_label_folder")]

  for builder in builders:
    mod_name = builder.__class__.__module__
    modules = mod_name.split(".")
    if "testing" in modules:
      continue

    current_mod_ctr = module_to_builder
    for mod in modules:
      current_mod_ctr = current_mod_ctr[mod]
    current_mod_ctr.append(builder)

  module_to_builder = module_to_builder["tensorflow_datasets"]
  return module_to_builder


def make_feature_information(info):
  """Make feature information table."""
  return FEATURE_BLOCK % info.features


def make_citation(citation):
  return CITATION_BLOCK % citation.strip() if citation else ""


def make_statistics_information(info):
  """Make statistics information table."""
  if not info.splits.total_num_examples:
    # That means that we have yet to calculate the statistics for this.
    return "None computed"

  stats = [(info.splits.total_num_examples, "ALL")]
  for split_name, split_info in info.splits.items():
    stats.append((split_info.num_examples, split_name.upper()))
  # Sort reverse on number of examples.
  stats.sort(reverse=True)
  stats = "\n".join([
      "{0:10} | {1:>10,}".format(name, num_exs) for (num_exs, name) in stats
  ])
  return STATISTICS_TABLE.format(split_statistics=stats)


def dataset_docs_str(datasets=None):
  """Create dataset documentation string for given datasets.

  Args:
    datasets: list of datasets for which to create documentation.
              If None, then all available datasets will be used.

  Returns:
    - overview document
    - a dictionary of sections. Each dataset in a section is represented by a
    pair (dataset_name, string describing the datasets (in the MarkDown format))
  """

  module_to_builder = make_module_to_builder_dict(datasets)
  sections = sorted(list(module_to_builder.keys()))
  section_docs = collections.defaultdict(list)

  for section in sections:
    builders = tf.nest.flatten(module_to_builder[section])
    builders = sorted(builders, key=lambda b: b.name)
    builder_docs = [
        (builder.name, document_single_builder(builder)) for builder in builders
    ]
    section_docs[section.capitalize()] = builder_docs
  return [DOC, section_docs]


SCHEMA_ORG_PRE = """\
<div itemscope itemtype="http://schema.org/Dataset">
  <div itemscope itemprop="includedInDataCatalog" itemtype="http://schema.org/DataCatalog">
    <meta itemprop="name" content="TensorFlow Datasets" />
  </div>
"""

SCHEMA_ORG_NAME = """\
  <meta itemprop="name" content="{val}" />
"""

SCHEMA_ORG_URL = """\
  <meta itemprop="url" content="https://www.tensorflow.org/datasets/catalog/{val}" />
"""

SCHEMA_ORG_DESC = """\
  <meta itemprop="description" content="{val}" />
"""

SCHEMA_ORG_SAMEAS = """\
  <meta itemprop="sameAs" content="{val}" />
"""

SCHEMA_ORG_POST = """\
</div>
"""


def schema_org(builder):
  # pylint: disable=line-too-long
  """Builds schema.org microdata for DatasetSearch from DatasetBuilder.

  Markup spec: https://developers.google.com/search/docs/data-types/dataset#dataset
  Testing tool: https://search.google.com/structured-data/testing-tool
  For Google Dataset Search: https://toolbox.google.com/datasetsearch

  Microdata format was chosen over JSON-LD due to the fact that Markdown
  rendering engines remove all <script> tags.

  Args:
    builder: `tfds.core.DatasetBuilder`

  Returns:
    HTML string with microdata
  """
  # pylint: enable=line-too-long

  properties = [
      (lambda x: x.name, SCHEMA_ORG_NAME),
      (lambda x: x.description, SCHEMA_ORG_DESC),
      (lambda x: x.name, SCHEMA_ORG_URL),
      (lambda x: (x.urls and x.urls[0]) or "", SCHEMA_ORG_SAMEAS)
  ]

  info = builder.info
  out_str = SCHEMA_ORG_PRE
  for extractor, template in properties:
    val = extractor(info)
    if val:
      # We are using cgi module instead of html due to Python 2 compatibility
      val = cgi.escape(val, quote=True)
      val = val.replace("\n", "&#10;")
      val = val.strip()
      out_str += template.format(val=val)
  out_str += SCHEMA_ORG_POST

  return out_str


def main(_):
  print(dataset_docs_str())


if __name__ == "__main__":
  app.run(main)
