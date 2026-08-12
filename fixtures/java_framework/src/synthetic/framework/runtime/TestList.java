package synthetic.framework.runtime;

public class TestList {
  public TestList setupBegin(String condition) {
    return this;
  }

  public TestList setupEnd(String condition) {
    return this;
  }

  public TestList addAction(Class<?> actionClass, String name) {
    return this;
  }

  public TestList setLevel(String condition) {
    return this;
  }

  public TestCaseBase addTestCase(String type, String configPath, String section) {
    return new TestCaseBase();
  }
}