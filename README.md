# EKG Store

`Alpha`

## Running
Setting up the development environment:

### 1. Requirements
> Skip the requirements that you already have.

- Install Inkscape and make sure it is in your system `PATH`. On OSX, you can use `brew cask install inkscape`, while on other systems please follow the official documentation.

### 2. Installing the Commandline Utility
- Execute `python setup.py develop` to install the development package. 
- To run tests, first install few other essential. Execute `pip install -r requirements.txt`.
- The tests are written using `nose`, a Python testing library. Run tests by executing `nosetests`.

### 3. Using Commandline Utility
This module also installs a commandline utility that can be used to process files from any location in filesystem.

- At any point, execute `ekgstore --help` to get the usage reference.
- To process files in a directory, execute `ekgstore <input dir> <output dir>`.
- To process all the files in current directory and store the result in the same, run `ekgstore . .`, where `.` refers to the current directory.

## Notes
**Scaling Factor**: We obtain the scaling factor from the length and height of the "caliberation marker" at the left side of pdf. Further, we have assumed that the ECG is caliberated at Standard settings.


## Collaboration
### Working on new features
Please ensure you create your new feature branch for any changes you make in code. After you're done, open a pull request to merge to master branch. Please *never* push directly on `master`.

### Coding Standards
We try to closely follow PEP8 coding guidelines with following exceptions:
- Indentation is strictly 2-space. Please do not use `tabs` or 4-space indents.
- Single letter, or nondescriptive variable names are prohibited unless they are used within loops, comprehensions, or lambda functions.
- Lines can be up to 120 characters long. Anything longer than that, you should immediately consider refactoring.
- Long functional chains are allowed, but each atomic call must be in a separate line with double hanging indent. Example:
```python
# Good
text_anchor_els = (self.svg
    .find('path')
    .parent()
    .next('g')
    .find('text'))

# Bad - Single hanging Indent
text_anchor_els = (self.svg
  .find('path')
  .parent()
  .next('g')
  .find('text'))

# Worse - Long chain
text_anchor_els = self.svg.find('path').parent().next('g').find('text')
```
- Do not use _obvious_ variable names that derive from their type. Example:
```python
# No!
element_list = [...]
# Instead use
elements = [...]
```

## Resources
### Module Specific
- Inkscape commandline reference: https://inkscape.org/en/doc/inkscape-man.html
- PyQuery API reference: http://pyquery.readthedocs.io/en/latest/api.html
- CSS Selectors syntax guide: https://api.jquery.com/category/selectors/
- Attribute Selectors guide: https://developer.mozilla.org/en/docs/Web/CSS/Attribute_selectors
- Comprehensions: http://python-3-patterns-idioms-test.readthedocs.io/en/latest/Comprehensions.html

### General
- PEP 8 reference: https://www.python.org/dev/peps/pep-0008/
- Python 3 docs: https://docs.python.org/3/
- Python 2 and Python 3 differences: https://wiki.python.org/moin/Python2orPython3
- Python 3 tutorials: http://docs.python-guide.org/en/latest/
