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
 * Generated example test method for example_module.
 */
public class ExampleGeneratedTestMethod extends BaseTestMethod {
  @Override
  protected void defineTestSequences(TestListManager testListManager) {
    String paramFile = "testtables/Example.toml";
    ConfigBlock config = ConfigLoader.load(paramFile, "example_module.ConditionsAndGradeables");

    String endCondition = config.getString("endCondition");
    String[] testConditions = config.getStringArray("testConditions");
    String[] groupNames = config.getStringArray("gradeableLists");

    TestList testList = testListManager.create("example_module_workflow");

    for (int i = 0; i < testConditions.length; i++) {
      String condition = testConditions[i];
      testList.setupBegin(condition)
          .addAction(LevelChangeAction.class, "Begin_" + condition)
          .setLevel(condition);

      List<String> groupEntries = config.getStringList(groupNames[i]);
      for (String entry : groupEntries) {
        String path = "example_module." + entry;
        ConfigBlock testCaseConfig = ConfigLoader.load(paramFile, path);
        String testCaseType = testCaseConfig.getString("testCase");
        TestCaseBase testCase = testList.addTestCase(
            Class.forName(testCaseType).asSubclass(TestCaseBase.class),
            paramFile,
            path
        );
        testCase.defineTestSequence();
      }

      testList.setupEnd(condition)
          .addAction(LevelChangeAction.class, "End_" + condition)
          .setLevel(endCondition);
    }
  }
}