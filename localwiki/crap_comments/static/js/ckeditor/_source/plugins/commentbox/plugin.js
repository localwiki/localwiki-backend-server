(function()
{
	CKEDITOR.plugins.add( 'commentbox',
	{
		requires : [ 'wikiplugins' ],

		beforeInit : function( editor )
		{
            /* Only enable this plugin in Davis region & user pages for now */
            if (region_slug != 'davis' || window.location.pathname.toLowerCase().indexOf('/users/') != 0) {
                return;
            }
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
            /* Only enable this plugin in Davis region & user pages for now */
            if (region_slug != 'davis' || window.location.pathname.toLowerCase().indexOf('/users/') != 0) {
                return;
            }
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
