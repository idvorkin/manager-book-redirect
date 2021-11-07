#!zsh
while true; do

        # woah - |& redirect stdout to tee - who knew!
        (time curl https://idvorkin.azurewebsites.net/topic\?t\=what-are-your-thoughts-on-a-pip) 2>&1 | tee -a ~/tmp/keepwarm.out.txt
        date | tee -a ~/tmp/keepwarm.out.txt
        sleep 60 # sleep for 5 minutes (which is I think what required to stay warm)

        # with a 1 minute sleep:
        # 60/hr * 24 hr/day *30 day/month
        # ~ 50K /month
        # App is 1.5GB, ~ excution is ~1s.
        # ~ 100K GB.s
        # https://azure.microsoft.com/en-us/pricing/details/functions/
        # Free: 1M requests, 400K GB*s
        # Still lots of headroom

done

