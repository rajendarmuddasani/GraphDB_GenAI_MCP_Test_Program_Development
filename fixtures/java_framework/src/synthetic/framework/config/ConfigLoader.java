package synthetic.framework.config;

public final class ConfigLoader {
  private ConfigLoader() {
  }

  public static ConfigBlock load(String configPath, String section) {
    return new ConfigBlock();
  }
}