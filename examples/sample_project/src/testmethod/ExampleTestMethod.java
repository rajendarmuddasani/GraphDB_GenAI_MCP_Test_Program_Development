package testmethod;

import framework.actions.LevelChangeAction;
import framework.config.ConfigBlock;
import framework.config.ConfigLoader;
import framework.runtime.BaseTestMethod;
import framework.runtime.TestCaseBase;
import framework.runtime.TestList;
import framework.runtime.TestListManager;
import java.util.List;

/**
 * Example configuration-driven test method for a public sample workflow.
 *
 * <p>This class shows how a generated test method can remain small while still
 * reading execution behavior from configuration.</p>
 * 
 * <h3>Configuration Structure:</h3>
 * <pre>
 * [example_module]
 * [example_module.ConditionsAndGradeables]
 * endCondition = "..."
 * testConditions = [...]
 * gradeableLists = [...]
 * </pre>
 * 
 * <h3>Test Flow:</h3>
 * <ol>
 *   <li>Read configuration from a structured config file</li>
 *   <li>Create a workflow list for the module</li>
 *   <li>For each test condition:
 *     <ul>
 *       <li>Set the requested operating condition</li>
 *       <li>Load and execute grouped test cases</li>
 *       <li>Restore the end condition</li>
 *     </ul>
 *   </li>
 * </ol>
 */
public class ExampleTestMethod extends BaseTestMethod {

  /**
   * Define test sequences by reading configuration and dynamically loading test cases.
   *
   * <p>This method demonstrates:</p>
   * <ul>
   *   <li>Configuration loading</li>
   *   <li>Dynamic test case loading via Class.forName()</li>
   *   <li>Condition transition handling</li>
   *   <li>Grouped test execution</li>
   * </ul>
   *
   * @param testListManager the manager responsible for creating and managing workflow lists
   * @throws ClassNotFoundException if a test case class specified in TOML cannot be found
   */
  @Override
  protected void defineTestSequences(TestListManager testListManager) {
    // Load the module configuration block used by this sample test method.
    String paramFile = "testtables/Example.toml";
    ConfigBlock config = ConfigLoader.load(paramFile, "example_module.ConditionsAndGradeables");

    String endCondition = config.getString("endCondition");
    String[] testConditions = config.getStringArray("testConditions");
    String[] gradeableLists = config.getStringArray("gradeableLists");

    TestList testList = testListManager.create("example_module_workflow");

    for (int i = 0; i < testConditions.length; i++) {
      String tc = testConditions[i];

      testList.setupBegin(tc)
          .addAction(LevelChangeAction.class, "Begin_" + tc)
          .setLevel(tc);

      List<String> gradeablesForCondition = config.getStringList(gradeableLists[i]);
      
      for (String gradeable : gradeablesForCondition) {
        String path = "example_module." + gradeable;

        try {
          ConfigBlock testCaseConfig = ConfigLoader.load(paramFile, path);
          String testCaseType = testCaseConfig.getString("testCase");

          TestCaseBase testCase = testList.addTestCase(
              Class.forName(testCaseType).asSubclass(TestCaseBase.class),
              paramFile,
              path
          );
          
          testCase.defineTestSequence();
          
        } catch (ClassNotFoundException e) {
          throw new RuntimeException("Test case class not found: " + gradeable, e);
        }
      }

      testList.setupEnd(tc)
          .addAction(LevelChangeAction.class, "End_" + tc)
          .setLevel(endCondition);
    }
  }
}
