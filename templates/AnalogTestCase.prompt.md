---
mode: 'agent'
model: GPT-4.1
tools: ['search/codebase']
description: 'Generate a generic measurement-oriented Java test case from graph and configuration context'
---

# Generate a generic measurement-oriented test case using public-safe framework-neutral structure

# Use repository context, configuration files, and graph-backed project metadata when available.

## Recommended workflow

1. **Identify the required framework roles** from the project:
   - `BaseMeasurementCase`
   - `GradeableGroup`
   - `FunctionalPatternAction`
   - `CurrentMeasurementAction`
   - `VoltageMeasurementAction`
   - `MeasurementDescriptor`
   - `PatternExecutionMode`

2. **Use graph or repository context** to locate the current examples and configuration-driven cases that resemble the requested output.

3. **Read the measurement configuration**:
   - identify the test condition,
   - identify measurement signals,
   - identify patterns, labels, and thresholds,
   - identify whether each measurement is voltage-forced or current-forced.

4. **Report findings before generation**:
   - list the framework roles found,
   - summarize the measurement configuration,
   - note any missing assumptions.

## Documentation Guidelines

- **Class-level Javadoc**: Explain the measurement flow, configuration-driven inputs, and expected execution pattern in neutral terms.
- **Method-level Javadoc**: Describe how each measurement step is created from configuration.
- **Inline comments**: Keep them sparse and explanatory.
- **STRICT RULE**: Do not hardcode environment-specific identifiers into comments.
- **IMPORT RULE**: Use explicit imports only.

```java
package sample.measurement;

import framework.actions.CurrentMeasurementAction;
import framework.actions.FunctionalPatternAction;
import framework.actions.FunctionalPatternAction.PatternExecutionMode;
import framework.actions.VoltageMeasurementAction;
import framework.reporting.MeasurementDescriptor;
import framework.runtime.BaseMeasurementCase;
import framework.runtime.GradeableGroup;

public class ExampleAnalogMeasurementCase extends BaseMeasurementCase {

  public String testCondition;
  public String signalName;
  public int averaging;
  public double settlingTime;

  public String[] patterns;
  public MeasurementDescriptor[] patternDescriptors;
  public MeasurementDescriptor[] measurementDescriptors;
  public String[] measurementTypes;
  public double[] thresholds;

  @Override
  public void defineTestSequence() {
    final String suffix = testCondition.substring(testCondition.length() - 3).toLowerCase();

    for (int i = 0; i < patterns.length; i++) {
      final String measurementName = "meas" + i;
      final String groupName = measurementName + "_" + suffix;
      final GradeableGroup group = testList.addGroup(groupName);

      group.addAction(FunctionalPatternAction.class, measurementName + "_pattern_" + suffix, patternDescriptors[i])
        .setPattern(patterns[i], PatternExecutionMode.SKIP);

      if ("vfim".equalsIgnoreCase(measurementTypes[i])) {
        group.addAction(VoltageMeasurementAction.class, measurementName + "_measure_" + suffix, measurementDescriptors[i])
          .setSignal(signalName)
          .setThreshold(thresholds[i])
          .setAverage(averaging)
          .setSettlingTime(settlingTime);
      } else {
        group.addAction(CurrentMeasurementAction.class, measurementName + "_measure_" + suffix, measurementDescriptors[i])
          .setSignal(signalName)
          .setThreshold(thresholds[i])
          .setAverage(averaging)
          .setSettlingTime(settlingTime);
      }
    }
  }
}
```