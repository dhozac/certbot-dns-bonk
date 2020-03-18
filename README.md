# Certbot plugin for completing DNS challenges using bonk

This is a plugin for [Certbot](https://certbot.eff.org/) that uses
[bonk's API](https://github.com/dhozac/bonk) to authenticate certificate
requests using the dns-01 challenge.

## Usage

1. Install the plugin and certbot: `pip3 install certbot certbot-dns-bonk`

2. Create a bonk.ini file containing your credentials, the URL to your bonk
   instance, and the group that your user is in to maintain control of the
   records:
   ```
   certbot_dns_bonk:dns_bonk_endpoint=https://SOCRATES/bonk
   certbot_dns_bonk:dns_bonk_username=USERNAME
   certbot_dns_bonk:dns_bonk_password=PASSWORD
   certbot_dns_bonk:dns_bonk_group=GROUP
   certbot_dns_bonk:dns_bonk_cleanup_action=record
   ```

   If cleanup_action is record, records will be deleted after each run. If your
   user lacks permission to create records on its own in the zones, set this to
   value instead, which will only delete the values it has added.

   Make sure this file is only readable by the user running certbot, typically
   root.

3. Run `certbot` using the plugin, e.g.
   ```
   certbot certonly -a certbot-dns-bonk:dns-bonk --certbot-dns-bonk:dns-bonk-credentials /PATH/TO/bonk.ini -d DOMAIN
   ```

4. Set up automatic renewal as a cron job, e.g.
   ```
   certbot renew -q -a certbot-dns-bonk:dns-bonk --certbot-dns-bonk:dns-bonk-credentials /PATH/TO/bonk.ini -d DOMAIN
   ```
