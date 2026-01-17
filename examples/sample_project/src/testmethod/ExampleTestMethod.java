package testmethod;

import brick.IChangeLevelBrick;
import testmethod.TlistBaseTm;
import tlist.ITListManager;
import tlist.ITlist;
import parametrization.IBlockParams;
import parametrization.Param;
import testcase.TlistTestCase;
import java.util.List;

/**
 * Example generic TOML-driven test method demonstrating knowledge graph ingestion patterns.
 * 
 * <p>This is a sanitized example showing the structure of generated test methods without
 * proprietary implementation details.</p>
 * 
 * <h3>TOML Configuration Structure:</h3>
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
 *   <li>Read configuration from TOML file</li>
 *   <li>Create test list for the module</li>
 *   <li>For each test condition:
 *     <ul>
 *       <li>Setup begin with level change</li>
 *       <li>Load and execute gradeables</li>
 *       <li>Setup end with level change</li>
 *     </ul>
 *   </li>
 * </ol>
 * 
 * @see TlistBaseTm
 * @see TlistTestCase
 * @see IChangeLevelBrick
 */
public class ExampleTestMethod extends TlistBaseTm {

  /**
   * Define test sequences by reading TOML configuration and dynamically loading test cases.
   * 
   * <p>This method demonstrates:</p>
   * <ul>
   *   <li>TOML parameter reading</li>
   *   <li>Dynamic test case loading via Class.forName()</li>
   *   <li>Level change automation</li>
   *   <li>Gradeable execution</li>
   * </ul>
   * 
   * @param tlistManager the TList manager for creating and managing test lists
   * @throws ClassNotFoundException if a test case class specified in TOML cannot be found
   */
  @Override
  protected void defineTestSequences(ITListManager tlistManager) {
    // Read TOML configuration
    String paramFile = "testtables/Example.toml";
    IBlockParams cfg = Param.testParam().getParams(paramFile, "example_module.ConditionsAndGradeables");

    // Extract test conditions from TOML
    String endCondition = cfg.getString("endCondition");
    String[] testConditions = cfg.getStringArray("testConditions");
    String[] gradeableLists = cfg.getStringArray("gradeableLists");

    // Create test list for example module
    ITlist tlist = tlistManager.create("example_module_tests");

    // Iterate through each test condition
    for (int i = 0; i < testConditions.length; i++) {
      String tc = testConditions[i];

      // Setup begin: change level to test condition
      tlist.setupBegin(tc)
          .addBrick(IChangeLevelBrick.class, "Begin_" + tc)
          .setLevel(tc);

      // Get gradeables for this test condition
      List<String> gradeablesForCondition = cfg.getStringList(gradeableLists[i]);
      
      // Add each gradeable test case dynamically
      for (String gradeable : gradeablesForCondition) {
        String path = "example_module." + gradeable;

        try {
          // Read test case configuration from TOML
          IBlockParams gbParams = Param.testParam().getParams(paramFile, path);
          String testCaseType = gbParams.getString("testCase");

          // Dynamic class loading: instantiate test case from TOML
          TlistTestCase testCase = tlist.addTestCase(
              Class.forName(testCaseType).asSubclass(TlistTestCase.class), 
              paramFile, 
              path
          );
          
          // Execute test case sequence
          testCase.defineTestSequence();
          
        } catch (ClassNotFoundException e) {
          throw new RuntimeException("Test case class not found: " + gradeable, e);
        }
      }

      // Setup end: change level back to nominal
      tlist.setupEnd(tc)
          .addBrick(IChangeLevelBrick.class, "End_" + tc)
          .setLevel(endCondition);
    }
  }
}
