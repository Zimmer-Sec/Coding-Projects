# Setting Up Windows Server Without Personal Information

There are many different versions of Windows Server.
- "For the Masses": Server NT 3.5 / NT 4
- Enterprise: Server 2000 / 2003
- Data Center-focused: Server 2008 / 2012
- Cloud-focused: Server 2016 / 2019 / 2022 / 2025

------------------------------------------------------
While the Windows Server 2025 might be a bit overkill for my virtual needs, I chose to go with it for the security enhancements and additional features to play around with. Now to choose the edition of Server 2025:
- Datacenter Edition: Best for extensive virtualization and cloud environments, offering unlimited virtual instances and advanced features. Includes VBS enclaves for security.
- Standard Edition: for small organizations with fewer virtual instances. Includes all essential server features along with VBS enclaves for security.
    - https://learn.microsoft.com/en-us/windows-server/get-started/editions-comparison?pivots=windows-server-2025

-------------------------------------------------

Going with standard edition was an easy decision. I won't be merging my setup to a hybrid solution and I won't be needing anything fancy. Lastly, I could choose between a GUI-based server experience (requires more resources) or a headless experience for terminal-based management.
- Desktop Experience
- Server Core (Headless SConfig and Powershell-based)

-------------------------------------------------

After deciding on Windows Server 2025 Standard Edition Desktop Experience, I continued on with installing the 180-day trial without any personal information:

1. Navigate to Microsoft's [Windows Server 2025 Overview](https://www.microsoft.com/en-us/evalcenter/evaluate-windows-server-2025) and click "Download the ISO"  
2. Retrieve a free temporary number from [Quackr](https://quackr.io/) and a free temporary email address from [TempMail](https://temp-mail.org/en/). Enter it with random information to get the ISO download.
3. Once downloaded, head into VirtualBox or whatever other hypervisor you use and create a new virtual machine with the ISO image you just downloaded.
- !! Note: Even after meeting the OS' hardware requirement [minimums](https://learn.microsoft.com/en-us/windows-server/get-started/hardware-requirements?tabs=cpu&pivots=windows-server-2025) I had issues getting it to boot fully. Adding more than 4GB RAM (I went with 8GB) and adding 3 CPU cores fixed this.
- !! Note: Be sure to **de-select** "Proceed with Unattended Installation" when configuring the ISO! This will bypass the option to select desktop experience or headless and ship you straight to SConfig on Server Core.

<img width="1085" height="801" alt="image" src="https://github.com/user-attachments/assets/b071327c-d0b9-48e6-b2a9-bf5769a816b8" />

4. Boot it and get through the setup process to create your built-in Administrator account's credentials:

<img width="1049" height="866" alt="image" src="https://github.com/user-attachments/assets/e184c541-a5f3-431a-abb7-e526f595db8c" />






Resources:
- [Windows Server 2025 Administration Fundamentals - Fourth Edition](https://learning.oreilly.com/library/view/windows-server-2025/9781836205012/)
- 
