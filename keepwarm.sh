#!zsh
while true; do

        # woah - |& redirect stdout to tee - who knew!
        (time http https://manager-book.azurewebsites.net/topic\?t\=what-are-your-thoughts-on-a-pip) 2>&1 | tee -a ~/tmp/keepwarm.out.txt
        date | tee -a ~/tmp/keepwarm.out.txt
        sleep 600 # sleep for 5 minutes (which is I think what required to stay warm)

            # per month
            # 12/hr * 24 hr/day *30 day/month
            # ~ 5K /month

done

