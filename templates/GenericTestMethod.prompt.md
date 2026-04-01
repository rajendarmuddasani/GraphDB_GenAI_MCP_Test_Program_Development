---
mode: 'agent'
model: GPT-4.1
tools: ['search/codebase']
description: 'Generate a configuration-driven Java test method from graph and file context'
---

# Generate a Java test method that reads runtime behavior from configuration instead of hardcoded arrays

# Use repository context, configuration files, and graph-backed project metadata when available. Do not assume unpublished internal package names or private framework classes.

## Recommended workflow

1. **Identify the required framework roles** from the target project:
   - `BaseTestMethod`
   - `TestCaseBase`
   - `LevelChangeAction`
   - `TestList`
   - `TestListManager`
   - `ConfigBlock`
   - `ConfigLoader`

2. **Inspect graph or repository context** for version-specific structure:
   - find the current base test method,
   - locate related helper classes,
   - identify any reusable examples already present in the codebase.

3. **Read the configuration source** that drives the generated method:
   - collect the module key,
   - enumerate test conditions,
   - enumerate gradeable groups,
   - identify referenced test case classes and parameters.

4. **Report findings before generation**:
   - list the framework roles you found,
   - list the configuration sections used,
   - note any missing context or assumptions.

## Documentation Guidelines

- **Class-level Javadoc**: Explain the goal of the generated test method, the configuration sections it consumes, and the execution flow at a framework-neutral level.
- **Method-level Javadoc**: Describe how configuration is read, how conditions are iterated, and how test cases are instantiated dynamically.
- **Inline comments**: Explain only the non-obvious steps.
- **STRICT RULE**: Do not hardcode environment-specific values into comments or generated structure.
- **IMPORT RULE**: Use explicit imports only.

## Configuration Reference (INPUT ONLY - DO NOT GENERATE)
```toml
[{MODULE}]

[{MODULE}.ConditionsAndGradeables]
endCondition = "NominalCondition"
testConditions = ["MaxCondition", "MinCondition"]
gradeableLists = ["max", "min"]
max = ["{gradeable1}.max", "{gradeable2}.max", "{gradeable3}.max", "{gradeable4}.max"]
min = ["{gradeable5}.min"]

[{MODULE}.{gradeable1}.max]
testCase = "framework.tests.PatternDrivenCase"
patternNames = ["patterns.{pattern1}"]
label = "quality_gate_1"

[{MODULE}.{gradeable5}.min]
testCase = "framework.tests.{TestCaseClass}"
testCaseParams = ["{param1}", "{param2}"]

# ... additional gradeable sections
```

### Required Structure
```java
import framework.actions.LevelChangeAction;
import framework.config.ConfigBlock;
import framework.config.ConfigLoader;
import framework.runtime.BaseTestMethod;
import framework.runtime.TestCaseBase;
import framework.runtime.TestList;
import framework.runtime.TestListManager;
import java.util.List;

public class {ClassName} extends BaseTestMethod {
  @Override
  protected void defineTestSequences(TestListManager testListManager) {
    String paramFile = "modules/{module}/testtables/{Module}.toml";
    ConfigBlock config = ConfigLoader.load(paramFile, "{module}.ConditionsAndGradeables");

    String endCondition = config.getString("endCondition");
    String[] testConditions = config.getStringArray("testConditions");
    String[] gradeableLists = config.getStringArray("gradeableLists");

    TestList testList = testListManager.create("{module}_workflow");

    for (int i = 0; i < testConditions.length; i++) {
      String tc = testConditions[i];

      testList.setupBegin(tc)
          .addAction(LevelChangeAction.class, "Begin_" + tc)
          .setLevel(tc);

      List<String> gradeablesForCondition = config.getStringList(gradeableLists[i]);
      for (String gradeable : gradeablesForCondition) {
        String path = "{module}." + gradeable;

        ConfigBlock testCaseConfig = ConfigLoader.load(paramFile, path);
        String testCaseType = testCaseConfig.getString("testCase");

        TestCaseBase testCase = testList.addTestCase(
            Class.forName(testCaseType).asSubclass(TestCaseBase.class),
            paramFile,
            path
        );
        testCase.defineTestSequence();
      }

      testList.setupEnd(tc)
          .addAction(LevelChangeAction.class, "End_" + tc)
          .setLevel(endCondition);
    }
  }
}
```