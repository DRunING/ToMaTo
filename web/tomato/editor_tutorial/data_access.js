var editor_tutorial = [
			{
			text:	'<p class="tutorialExplanation">\
						Welcome to the Data Access tutorial!<br />\
						This tutorial will teach you how you can upload and/or download data to or from your devices.</p>\
					<p class="tutorialExplanation">\
						Let\'s assume you have created this topology, and now you need to put files on your devices to execute your experiment.</p>\
					<p class="tutorialExplanation">\
						<i>This tutorial requires knowledge which has been taught in the beginners\' tutorial, and a basic knowledge about the Linux command line (especially ifconfig, ssh, and scp)</i></p>',
			skip_button: 'Start tutorial'
			},
			{
			trigger:function(obj) {
						
				mask = {
					action: "prepare",
					component: "element",
					operation: "action",
					phase: "begin"
				};
				return compareToMask(obj,mask);
				
			  },
			text:	'<p class="tutorialExplanation">\
						Currently, your topology does only exist as a "plan". This means, that devices do not have any hard drive images or similar.</p>\
					<p class ="tutorialExplanation">\
						When you prepare the devices, those images will be created from the templates.</p>\
					<p class="tutorialCommand">\
						Prepare your topology\'s devices.</p>'
			},
			{
			text:	'<p class="tutorialExplanation">\
						Wait for both devices to be prepared. Then press "Continue" button.</p>',
			skip_button: "Continue"
			},
			{
			trigger:function(obj) { 
				
				mask = {
					action: 'download_grant',
					component: "element",
					operation: "action",
					phase: "end"
				};
				return compareToMask(obj,mask);
			
			  },
			text:	'<p class="tutorialExplanation">\
						Let\'s assume you have changed some files, and now you want to backup your device\'s disk image.<br />\
						You can download the disk image of any prepared device by right-clicking on the device and select "Download image".</p>\
					<p class="tutorialCommand">\
						Download a disk image.</p>\
					<p class="tutorialExplanation">\
						Warning: The download might be big. Skip this step if you are on a metered connection!</p>'
			},
			{
			trigger:function(obj) {	
				mask = {
					action: 'upload_use',
					component: "element",
					operation: "action",
					phase: "end"
				};
				return compareToMask(obj,mask);
			
			  },
			text:	'<p class="tutorialExplanation">\
						The download might take a bit longer.</p>\
					<p class="tutorialExplanation">\
						You can upload any image to a device of the same technology. You can not use images accross technologies (e.g., you can\'t upload an OpenVZ image to a KVM device, and vice versa).</p>\
					<p class="tutorialCommand">\
						Upload your image again.</p>\
					<p class="tutorialExplanation">\
						Again, skip this step if a big upload might cause you any troubles.</p>\
					<p class="tutorialExplanation">\
						The tutorial will continue after the upload has been finished.<br />\
						If you need to create multiple devices with certain modifications to their template,\
						creating the image in one device, and then distributing it to many might be the best method to accomplish this.</p>'
			},
			{
			text:	'<p class="tutorialExplanation">\
						In the "Devices" tab, on the right side, you can find "upload own images" devices.<br />\
						When you place such a device on your topology, it will be prepared immediately, and then you\'ll be asked to upload an image</p>\
					<p class="tutorialCommand">\
						Place suche a device on your topology (cancel the upload if you want). After this, click "Continue"</p>\
					<p class="tutorialExplanation">\
						Ignore this device for the rest of the tutorial, or delete it.</p>',
			skip_button: "Continue"
			},
			{
			trigger:function(obj) { 
					
				mask = {
					attrs: {
						state: "created",
						type: "external_network"
					},
					component: "element",
					operation: "create",
					phase: "end"
				};
				return compareToMask(obj,mask);
			
			  },
			text:	'<p class="tutorialExplanation">\
						The easiest way to transmit files to or from your devices is the internet.</p>\
					<p> class ="tutorialExplanation">\
						Devices don\'t have an internet connection by default. To connect them, the first thing you need to do is to create an internet interface</p>\
					<p class="tutorialCommand">\
						Add an "Internet" to your topology. You can find it in the "Home" tab.</p>',
			},
			{
			trigger:function(obj) { 
				console.log("TODO: check if this is a connection between the Internet and a device");
				mask = {
					attrs: {
						state: "created",
					},
					component: "connection",
					operation: "create",
					phase: "end"
				};
				return compareToMask(obj,mask);
				
			  },
			text:	'<p class="tutorialCommand">\
						Now, connect your devices with the internet.</p>',
			},
			{
			trigger:function(obj) { 
				console.log("TODO: check if this is a connection between the Internet and a device");
				mask = {
					attrs: {
						state: "created",
					},
					component: "connection",
					operation: "create",
					phase: "end"
				};
				return compareToMask(obj,mask);
				
			  },
			text:	'<p class="tutorialCommand">\
						Also, connect the other device to the internet.</p>',
			},
				
			{
			trigger:function(obj) {
						
				mask = {
					action: "start",
					component: "element",
					operation: "action",
					phase: "begin"
				};
				return compareToMask(obj,mask);
				
			  },
			text:	'<p class="tutorialExplanation">\
						<i>In case you wonder about the different look of the connections: You\'ll learn more about this in the "Connections" tutorial. You can ignore it in this tutorial.</i></p>\
					<p class="tutorialExplanation">\
						Of course your devices must be running to be able to access the internet.</p>\
					<p class="tutorialCommand">\
						Start your topology\'s devices.</p>'
			},
			{
			text:	'<p class="tutorialExplanation">\
						Wait for both all devices to be running. Then press "Continue" button.</p>',
			skip_button: "Continue"
			},
			{
					trigger:function(obj) {
						
						mask = {
							component: "element",
							operation: "console-dialog"
						};
						return compareToMask(obj,mask);
						
					  },
			text:	'<p class="tutorialCommand">\
						Please open a terminal connection to one of your devices.</p>'
			},
			{
			text:	'<p class="tutorialExplanation">\
						You should now be able to ping any server in the Internet. Try it! You can also see your device\'s global IP address using commands like ifconfig.</p>\
					<p class="tutorialExplanation">\
						If you need to install software, you can use your device\'s OS preferred way to do this.</p>',
			skip_button: "Continue"
			},
			{
			text:	'<p class="tutorialExplanation">\
						You might want to connect to the device using ssh or scp.</p>\
					<p class="tutorialExplanation">\
						Use the command "ssh-enable" to enable ssh access.<p>\
					<p class="tutorialExplanation">\
						You will be asked to set a root password. Using ifconfig, you can determine your global IP address. You can then connect to the device via ssh, or transmit data to or from it via scp (Try it!)</p>',
			skip_button: "Continue"
			},
			
			{
			text:	'<p class="tutorialExplanation">\
						That was it for this tutorial! More ways to access data will be coming soon.</p>'
			}
];