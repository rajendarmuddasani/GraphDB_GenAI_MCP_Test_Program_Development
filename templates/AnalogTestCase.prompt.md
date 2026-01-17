---
mode: 'agent'
model: GPT-4.1
tools: ['search/codebase', 'toolbox/get_datas_from_particular_ingestion_version']
description: 'Generate generic analog measurement test case - works for any IP module'
---

# Generate generic analog measurement test case using ONLY @ConfigParam
# Supports N measurements with functional patterns
# Works for IVR, ADC, PLL, bandgap, or any analog IP

# Use get_datas_from_particular_ingestion_version tool to fetch current Java templates (classes and Markdown linked to GitVersion with changeType != 'removed') - do not rely on static file references.

## Step-by-step data exploitation process:

1. **Identify required classes** from the template:
   - TlistTestCase (base class)
   - IGradeableBrick (gradeable container)
   - IFuncBrick (functional test brick)
   - IIfVmBrick (current measurement brick)
   - IVfImBrick (voltage measurement brick)
   - IDlogConfig (datalog configuration)
   - CallPfMode (pattern/opseq mode enum)

2. **Search in all_relations** for DESCRIBES relationships:
   - Filter relations where `type == "DESCRIBES"`
   - Match `startElementId` (markdown) with `endElementId` (Java class)
   - Extract markdown files that describe the classes listed above

3. **Find current module version**:
   - In `gitversions_classes`, locate entry where `moduleName == "libraries"`
   - Extract `modulePath` and `name` for reference
   - Note the `commit` and `timestamp` for traceability

4. **Validate markdown relevance**:
   - Cross-reference markdown `elementId` from step 2 with `markdowns` array
   - Prioritize markdowns with titles containing: "analog", "measurement", "vfim", "ifvm", "parametrization", "brick"
   - Use ONLY markdowns that have DESCRIBES links to classes you're using

5. **Report findings** before generation:
   - List classes found with their versions
   - List relevant markdown documentation identified via DESCRIBES relationships
   - Mention if any required class or documentation is missing

## Documentation Guidelines

- **Class-level Javadoc**: Provide comprehensive description of the test case's purpose, TOML configuration structure, and measurement flow. Explain the generic analog measurement approach without hardcoded examples.
- **Method-level Javadoc**: Detail the logic of defineTestSequence(), including parameter reading, gradeable creation, and dynamic measurement brick configuration.
- **Inline comments**: Explain key operations (pattern execution, measurement type selection, pin configuration) but keep concise.
- **STRICT RULE**: NEVER include hardcoded values, examples, or specific pin names/DLC numbers in comments - only describe the generic structure and flow.
- **IMPORT RULE**: Use explicit imports only - NO wildcard imports (no `.*`). Import each class individually (e.g., `import libraries.methodology.tlist.TlistTestCase;` instead of `import libraries.methodology.tlist.*;`).

```java
package libraries.ip.common.analog;

import libraries.methodology.tlist.parametrization.TlistTestCase;
import libraries.methodology.tlist.tlist.IGradeableBrick;
import libraries.methodology.tlist.brick.IFuncBrick;
import libraries.methodology.tlist.brick.IFuncBrick.CallPfMode;
import libraries.methodology.tlist.brick.IIfVmBrick;
import libraries.methodology.tlist.brick.IVfImBrick;
import libraries.platform.datalog.IDlogConfig;

public class TcIpGethIvr extends TlistTestCase {

  @ConfigParam public String testCondition;
  @ConfigParam public String pin;
  @ConfigParam public int averaging;
  @ConfigParam public double settlingTime;

  @ConfigParam public String[] patterns;
  @ConfigParam public IDlogConfig[] dlcPatterns;
  @ConfigParam public IDlogConfig[] dlcMeasurements;
  @ConfigParam public String[] measurementTypes;
  @ConfigParam public double[] clamps;

  @Override
  public void defineTestSequence() {
    final String suffix = testCondition.substring(testCondition.length() - 3).toLowerCase();

    for (int i = 0; i < patterns.length; i++) {
      final String measurementName = "meas" + i;
      final String gradeableName = measurementName + "_" + suffix;
      final IGradeableBrick gb = tlist.addGradeable(gradeableName);

      gb.addBrick(IFuncBrick.class, measurementName + "_func_" + suffix, dlcPatterns[i])
        .setOpSeq(patterns[i], CallPfMode.SKIP);

      if ("vfim".equalsIgnoreCase(measurementTypes[i])) {
        gb.addBrick(IVfImBrick.class, measurementName + "_meas_" + suffix, dlcMeasurements[i])
          .setForce(pin, 0.0)
          .setClamp(clamps[i])
          .setMeasure(pin, 0.0001)
          .setAverage(averaging)
          .setSettlingTime(settlingTime);
      } else {
        gb.addBrick(IIfVmBrick.class, measurementName + "_meas_" + suffix, dlcMeasurements[i])
          .setForce(pin, 0.0)
          .setClamp(0.0, clamps[i])
          .setMeasure(pin)
          .setAverage(averaging)
          .setSettlingTime(settlingTime);
      }
    }
  }
}
```