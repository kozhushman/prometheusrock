# Change Log

All notable changes to the "prometheusrock" middleware will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [0.1.1] - 06.11.2020
### Fixed
- [Issue #2](https://github.com/kozhushman/prometheusrock/issues/2)
### Added
- Opportunity to disable default metrics
- Updated README

## [0.1.3] - 10.12.2020
### Fixed
- [Issue #3](https://github.com/kozhushman/prometheusrock/issues/3)
### Added
- Opportunity to get access to `request` object in custom function

## [0.2.0] - 02.04.2021
### Added - Major Update
Recently I came across some log-overflow problems, and they must be fixed, 
so I decided to make some changes in this middleware.  
I will not delete some old args, 
despite some overlapping (`remove_labels` can be replaced with new `custom_base_labels` for example), - 
don't want to break API and functionality with this update.
- Init parameter`custom_base_labels` - if you want change default labels to yours - pass them here.
  **REWRITES DEFAULT LABLES**. Args `remove_labels` **WILL BE IGNORED**.   
  example - `['path','method']` - and you have metric, that contains only `path` and `method` labels.
- Init parameter `custom_base_headers` - if you want change default headers to yours - pass them here.
  **REWRITES DEFAULT HEADERS**. Args `additional_headers` **WILL BE IGNORED**.
  If you use `custom_base_labels`, don't forget to pass `headers` in it, 
  otherwise `custom_base_headers` will have no effect.  
  example - `['content-type','x-api-client']` - and now you write only these two headers.
- Init parameter `aggregate_paths` - if you have endpoints like `/item/{id}`, then, by default,
your logs will quickly overflow, showing you huge amount of numbers, when, in fact,
there is only one endpoint. So pass here list of endpoints path to aggregate by.  
example - `['/item/']`
