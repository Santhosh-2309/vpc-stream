import jenkins.model.*
import hudson.security.*

def instance = Jenkins.getInstance()
def hudsonRealm = new HudsonPrivateSecurityRealm(false)
hudsonRealm.createAccount("sandy", "san123")
instance.setSecurityRealm(hudsonRealm)
instance.setInstallState(jenkins.install.InstallState.INITIAL_SETUP_COMPLETED)
instance.save()
