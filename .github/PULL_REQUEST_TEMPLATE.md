## Description
Please include a summary of the changes and the related issue. Please also include relevant motivation and context.

Fixes # (issue link or number)

## Type of Change
Please delete options that are not relevant:
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update (non-breaking change to docs)

## Verification & Testing
Describe the tests that you ran to verify your changes. Provide instructions so we can reproduce.

- **Test A**: Compiled cleanly and ran lint tests: `python -m py_compile fluxmedia/*.py`
- **Test B**: Tested locally on [Windows / macOS / Linux / Termux]

## Checklist:
- [ ] My code follows the PEP 8 style guidelines of this project.
- My changes do not break backward compatibility.
- [ ] I have commented my code, particularly in hard-to-understand areas.
- [ ] I have updated the documentation in the `docs/` folder accordingly.
- [ ] I have repacked static web resources if I modified files in the `website/` folder (`python repack.py`).
- [ ] My changes generate no new warnings or type errors when running `npx pyright`.
