package synthetic.framework.config;

import java.util.Collections;
import java.util.List;

public class ConfigBlock {
  public String getString(String key) {
    return "synthetic";
  }

  public String[] getStringArray(String key) {
    return new String[] {"synthetic"};
  }

  public List<String> getStringList(String key) {
    return Collections.singletonList("synthetic");
  }
}