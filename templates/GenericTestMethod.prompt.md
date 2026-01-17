---
mode: 'agent'
model: GPT-4.1
tools: ['search/codebase', 'toolbox/get_datas_from_particular_ingestion_version']
description: 'Generate generic Java TestMethod with TOML-driven configuration'
---

# Generate Java class that reads all configuration from TOML - NO hardcoded arrays and no extra code other than required structure

# Use get_datas_from_particular_ingestion_version tool to fetch current Java templates (classes and Markdown linked to GitVersion with changeType != 'removed') - do not rely on static file references.

## Step-by-step data exploitation process:

1. **Identify required classes** from the template:
   - TlistBaseTm (base class)
   - TlistTestCase (test case base class)
   - IChangeLevelBrick (brick for level changes)
   - ITlist, ITListManager (test list interfaces)
   - IBlockParams (parameter reading)
   - Param (parameter access)

2. **Search in all_relations** for DESCRIBES relationships:
   - Filter relations where `type == "DESCRIBES"`
   - Match `startElementId` (markdown) with `endElementId` (Java class)
   - Extract markdown files that describe the classes listed above

3. **Find current module version**:
   - In `gitversions_classes`, locate entry where `moduleName == "{module}"` (e.g., "libraries")
   - Extract `modulePath` and `name` for reference
   - Note the `commit` and `timestamp` for traceability

4. **Validate markdown relevance**:
   - Cross-reference markdown `elementId` from step 2 with `markdowns` array
   - Prioritize markdowns with titles containing: "test_tables", "parametrization", "tlist", "brick", "dynamic_loading"
   - Use ONLY markdowns that have DESCRIBES links to classes you're using

5. **Report findings** before generation:
   - List classes found with their versions
   - List relevant markdown documentation identified via DESCRIBES relationships
   - Mention if any required class or documentation is missing

## Documentation Guidelines

- **Class-level Javadoc**: Provide comprehensive description of the test method's purpose, TOML configuration structure, and test flow. Explain the module, test conditions, gradeables, and dynamic test case loading generically without hardcoded examples.
- **Method-level Javadoc**: Detail the logic of defineTestSequences(), including parameter reading, test list creation, dynamic test case instantiation via Class.forName(), and gradeable execution.
- **Inline comments**: Explain key operations (TOML reading, level changes, dynamic class loading, test case addition) but keep concise.
- **STRICT RULE**: NEVER include hardcoded values, examples, or specific DLC numbers in comments - only describe the generic structure and flow.
- **IMPORT RULE**: Use explicit imports only - NO wildcard imports (no `.*`). Import each class individually (e.g., `import libraries.methodology.tlist.testmethod.TlistBaseTm;` instead of `import libraries.methodology.tlist.*;`).

## TOML Reference (INPUT ONLY - DO NOT GENERATE)
```toml
[{MODULE}]

[{MODULE}.ConditionsAndGradeables]
endCondition = "DpsLevNoVsNom"
testConditions = ["DpsLevNoVsMax", "DpsLevNoVsMin"]
gradeableLists = ["max", "min"]
max = ["{gradeable1}.max", "{gradeable2}.max", "{gradeable3}.max", "{gradeable4}.max"]
min = ["{gradeable5}.min"]

[{MODULE}.{gradeable1}.max]
testCase = "libraries.ip.common.func.TcFuncPattern"
patternNames = "modules.{module}.opseqs.{pattern1}"
dlc = "19000000"

[{MODULE}.{gradeable5}.min]
testCase = "modules.{module}.testmethods.{TestCaseClass}"
testCaseParams = ["{param1}", "{param2}"]

# ... additional gradeable sections
```

### Required Structure
```java
import libraries.methodology.tlist.brick.IChangeLevelBrick;
import libraries.methodology.tlist.testmethod.TlistBaseTm;
import libraries.methodology.tlist.tlist.ITListManager;
import libraries.methodology.tlist.tlist.ITlist;
import libraries.platform.parametrization.IBlockParams;
import libraries.platform.parametrization.Param;

public class {ClassName} extends TlistBaseTm {
  @Override
  protected void defineTestSequences(ITListManager tlistManager) {
    String paramFile = "modules/{module}/testtables/{Module}.toml";
    IBlockParams params = Param.testParam().getParams(paramFile, "{module}");
    IBlockParams cfg = Param.testParam().getParams(paramFile, "{module}.ConditionsAndGradeables");

    String endCondition = cfg.getString("endCondition");
    String[] testConditions = cfg.getStringArray("testConditions");
    String[] gradeableLists = cfg.getStringArray("gradeableLists");

    ITlist tlist = tlistManager.create("{module}_func");

    for (int i = 0; i < testConditions.length; i++) {
      String tc = testConditions[i];

      tlist.setupBegin(tc)
          .addBrick(IChangeLevelBrick.class, "Begin_" + tc)
          .setLevel(tc);

      List<String> gradeablesForCondition = cfg.getStringList(gradeableLists[i]);
      for (String gradeable : gradeablesForCondition) {
        String path = "{module}." + gradeable;

        IBlockParams gbParams = Param.testParam().getParams(paramFile, path);
        String testCaseType = gbParams.getString("testCase");

        TlistTestCase testCase = tlist.addTestCase(Class.forName(testCaseType).asSubclass(TlistTestCase.class), paramFile, path);
        testCase.defineTestSequence();
      }

      tlist.setupEnd(tc)
          .addBrick(IChangeLevelBrick.class, "End_" + tc)
          .setLevel(endCondition);
    }
  }
}
```