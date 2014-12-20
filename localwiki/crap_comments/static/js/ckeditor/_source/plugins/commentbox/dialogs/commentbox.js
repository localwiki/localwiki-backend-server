/*
Sapling pagelink dialog
*/

CKEDITOR.dialog.add( 'commentbox', function( editor )
{
	var plugin = CKEDITOR.plugins.commentbox;

	return {
		title : 'Comment Box',
		minWidth : 300,
		minHeight : 150,
		contents : [
			{
				id : 'info',
				label : gettext('Comment Box'),
				title : gettext('Comment Box'),
				elements :
				[
					{
						type : 'text',
						id : 'code',
						label : gettext('Title:'),
						required: false,
						setup : function( data )
						{
							if ( data.code )
								this.setValue( data.code );
                            else
                                this.setValue( gettext('Comments:') );
						},
						commit : function( data )
						{
							data.code = this.getValue();
						}
					}
				]
			}
		],
		onShow : function()
		{
			var editor = this.getParentEditor(),
				selection = editor.getSelection(),
				element = null,
				data = { code : '' };
			if ( ( element = selection.getStartElement() )
					&& element.is( 'span' ) )
				selection.selectElement( element );
			else
				element = null;
			if( element )
			{
				this._.selectedElement = element;
				data.code = $(element.$).text();
			}
			this.setupContent( data );
		},
		onOk : function()
		{
			var attributes = {},
				data = {},
				me = this,
				editor = this.getParentEditor();

			this.commitContent( data );

			attributes['class'] = 'plugin comments';
			var style = [];
			var node = $(data.code);
			if ( !this._.selectedElement )
			{
				if(jQuery.trim(data.code) == '')
					return;
				// Create element if current selection is collapsed.
				var selection = editor.getSelection(),
					ranges = selection.getRanges( true );

				var text = new CKEDITOR.dom.text( data.code, editor.document );
				ranges[0].insertNode( text );
				ranges[0].selectNodeContents( text );
				selection.selectRanges( ranges );

				// Apply style.
				var style = new CKEDITOR.style( { element : 'span', attributes : attributes } );
				style.apply( editor.document );
				var selected = selection.getStartElement();
				ranges[0].setStartAfter( selected );
				ranges[0].setEndAfter( selected );
				selection.selectRanges( ranges );
			}
			else
			{
				// We're only editing an existing link, so just overwrite the attributes.
				var element = this._.selectedElement;

				element.setAttributes( attributes );
				element.setText( data.code );
			}
		},
	};
});
