(function()
{
	CKEDITOR.plugins.add( 'commentbox',
	{
		requires : [ 'wikiplugins' ],

		beforeInit : function( editor )
		{
			var config = editor.config;
			if(!config.wikiplugins_menu)
				config.wikiplugins_menu = {};
			config.wikiplugins_menu.commentbox =
				{
					label : gettext('Comment Box'),
					command : 'commentbox',
					icon : this.path + 'images/balloon-white.png'
				}
			
		},
		
		init : function( editor )
		{
			editor.addCommand( 'commentbox', new CKEDITOR.dialogCommand( 'commentbox' ) );
			CKEDITOR.dialog.add( 'commentbox', this.path + 'dialogs/commentbox.js' );
			editor.on( 'doubleclick', function( evt )
			{
				var element = evt.data.element;
				element = element.getAscendant('span', true);
				if ( element )
				{
					if( element.hasClass('plugin') && element.hasClass('comments') )
						evt.data.dialog =  'commentbox';
				}
			});
		}
	});
})();
