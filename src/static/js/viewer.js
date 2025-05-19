function clickHandler (fileName) {
	console.log("Processing......" + fileName);
	renderDoc(fileName);
}

function listfiles(container) {
    const xhr = new XMLHttpRequest();
    xhr.open("GET", "http://localhost:5001/convertPDF/listfiles", true);
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4 && xhr.status === 200) {
            const parser = new DOMParser();
            const xmlDoc = parser.parseFromString(xhr.responseText, "text/xml");

			console.log(xmlDoc);

            const files = xmlDoc.getElementsByTagName("file");
            container.innerHTML = ""; // Clear previous output

            for (let i = 0; i < files.length; i++) {
                const fullPath = files[i].textContent || "";
				console.log (fullPath);
                const fileName = fullPath.split("/").pop(); // Get just the file name

                const div = document.createElement("div");
                const a = document.createElement("a");
                a.href = `javascript:clickHandler('${fileName}')`;
                a.textContent = fileName;

                div.appendChild(a);
                container.appendChild(div);
            }			
        } else if (xhr.readyState === 4) {
            console.error("Failed to load XML:", xhr.statusText);
        }
    };
    xhr.send();
}

function renderDoc(fileName) {
	$.ajax({url: "http://localhost:5001/convertPDF/xml_custom/" + fileName, success: function(response){
		console.log("The rest call was successful");

		var response = xmlToJson(response);
		var main_viewer = document.getElementById('main-viewer');
		$(main_viewer).empty();

		for (var l = 0; l < response.pages.page.length; l++) {
			console.log("Page: " + l);
			var page = response.pages.page[l]
			var page_coords = page.attributes.bbox.split(',');

			var page_ele = document.createElement("pre");
			page_ele.style.position = 'relative';
			page_ele.style.left = '10px';
			//page_ele.style.width = '90%';
			page_ele.style.width = (page_coords[2] - page_coords[0] + 1) + 'px';
			//page_ele.style.height = '850px';
			page_ele.style.minHeight = (page_coords[3] - page_coords[1] + 1) + 'px';
			page_ele.style['margin-bottom'] = '10px';

			main_viewer.appendChild(page_ele);



			sections = jsonPath(response.pages.page[l], "$..section[*]")

			for (var i = 0; i < sections.length; i++) {
				var section = sections[i];
				var section_coords = section.attributes.bbox.split(',');

				var section_ele = document.createElement("div");
				section_ele.setAttribute('class', 'ss-section');
				section_ele.style.position = 'absolute';

				section_ele.style.left = (section_coords[0] - page_coords[0]) + 'px';
				section_ele.style.top = (page_coords[3] - section_coords[3]) + 'px';

				section_ele.style.width = (section_coords[2] - section_coords[0] + 1 ) + 'px';
				section_ele.style.minHeight = (section_coords[3] - section_coords[1] + 1) + 'px';
				page_ele.appendChild(section_ele);

/*

				wordlist = jsonPath(section, "$..word[*]")

				for (var j = 0; j < wordlist.length; j++) {
					var wordLine = wordlist[j];
					var coordinates = wordLine.attributes.bbox.split(',');

					var diver = document.createElement("div");
					diver.setAttribute('class', 'ss-word');
					diver.innerHTML = wordLine['#text'];
					diver.style.color = 'black';
					diver.style.position = 'absolute';
					diver.style['font-size'] = wordLine.attributes.size + 'px';
					diver.style['font-family'] = wordLine.attributes.font;

					diver.style.left = (coordinates[0] - section_coords[0])  + 'px';
					diver.style.top = (section_coords[3]- coordinates[3]) + 'px'

					diver.style.width = (coordinates[2] - coordinates[0]) + 'px';
					diver.style.height = (coordinates[3] - coordinates[1]) + 'px';
					diver.style.overflow = 'hidden';
					section_ele.appendChild(diver);
				}

				fragments = jsonPath(section, "$..fragment[*]")
				console.log('initiating process of  fragments');
				for (var j = 0; j < fragments.length; j++) {
					console.log('found fragment');
					var fragment = fragments[j];
					var coordinates = fragment.attributes.bbox.split(',');

					var frg_ele = document.createElement("div");
					frg_ele.setAttribute('class', 'ss-fragment');
					frg_ele.style.position = 'absolute';

					frg_ele.style.left = (coordinates[0] - section_coords[0])  + 'px';
					frg_ele.style.top = (section_coords[3]- coordinates[3]) + 'px'
					frg_ele.style.width = (coordinates[2] - coordinates[0]) + 'px';
					frg_ele.style.height = (coordinates[3] - coordinates[1]) + 'px';
					section_ele.appendChild(frg_ele);
				}


				spacers = jsonPath(section, "$..spacer[*]")
				console.log('initiating process of  spacers');
				for (var j = 0; j < spacers.length; j++) {
					console.log('found spacers');
					var spacer = spacers[j];
					var coordinates = spacer.attributes.bbox.split(',');

					var sp_ele = document.createElement("div");
					sp_ele.setAttribute('class', 'ss-spacer');
					sp_ele.style.position = 'absolute';

					sp_ele.style.left = (coordinates[0] - section_coords[0])  + 'px';
					sp_ele.style.top = (section_coords[3]- coordinates[3]) + 'px'
					sp_ele.style.width = (coordinates[2] - coordinates[0]) + 'px';
					sp_ele.style.height = (coordinates[3] - coordinates[1]) + 'px';
					section_ele.appendChild(sp_ele);
				}
*/
			}


			segments = jsonPath(response.pages.page[l], "$..segment[*]")

			for (var i = 0; i < segments.length; i++) {
				var segment = segments[i];
				var segment_coords = segment.attributes.bbox.split(',');

				var segment_ele = document.createElement("div");
				segment_ele.setAttribute('class', 'ss-segment');
				segment_ele.style.position = 'absolute';

				segment_ele.style.left = (segment_coords[0] - page_coords[0]) + 'px';
				segment_ele.style.top = (page_coords[3] - segment_coords[3]) + 'px';

				segment_ele.style.width = (segment_coords[2] - segment_coords[0] + 1 ) + 'px';
				segment_ele.style.minHeight = (segment_coords[3] - segment_coords[1] + 1) + 'px';
				page_ele.appendChild(segment_ele);


				wordlist = jsonPath(segment, "$..word[*]")

				for (var j = 0; j < wordlist.length; j++) {
					var wordLine = wordlist[j];
					var coordinates = wordLine.attributes.bbox.split(',');

					var diver = document.createElement("div");
					diver.setAttribute('class', 'ss-word');
					diver.innerHTML = wordLine['#text'];
					diver.style.color = 'black';
					diver.style.position = 'absolute';
					diver.style['font-size'] = wordLine.attributes.size + 'px';
					diver.style['font-family'] = wordLine.attributes.font;

					diver.style.left = (coordinates[0] - segment_coords[0])  + 'px';
					diver.style.top = (segment_coords[3]- coordinates[3]) + 'px'

					diver.style.width = (coordinates[2] - coordinates[0]) + 'px';
					diver.style.height = (coordinates[3] - coordinates[1]) + 'px';
					diver.style.overflow = 'hidden';
					segment_ele.appendChild(diver);
				}

				fragments = jsonPath(segment, "$..fragment[*]")
				console.log('initiating process of  fragments');
				for (var j = 0; j < fragments.length; j++) {
					console.log('found fragment');
					var fragment = fragments[j];
					var coordinates = fragment.attributes.bbox.split(',');

					var frg_ele = document.createElement("div");
					frg_ele.setAttribute('class', 'ss-fragment');
					frg_ele.style.position = 'absolute';

					frg_ele.style.left = (coordinates[0] - segment_coords[0])  + 'px';
					frg_ele.style.top = (segment_coords[3]- coordinates[3]) + 'px'
					frg_ele.style.width = (coordinates[2] - coordinates[0]) + 'px';
					frg_ele.style.height = (coordinates[3] - coordinates[1]) + 'px';
					segment_ele.appendChild(frg_ele);
				}
			}

/*
			wordlist = jsonPath(page, "$..word[*]")

			for (var j = 0; j < wordlist.length; j++) {
				var wordLine = wordlist[j];
				var coordinates = wordLine.attributes.bbox.split(',');

				var diver = document.createElement("div");
				diver.setAttribute('class', 'ss-word');
				diver.innerHTML = wordLine['#text'];
				diver.style.color = 'black';
				diver.style.position = 'absolute';
				diver.style['font-size'] = wordLine.attributes.size + 'px';
				diver.style['font-family'] = wordLine.attributes.font;

				diver.style.left = (coordinates[0] - page_coords[0])  + 'px';
				diver.style.top = (page_coords[3]- coordinates[3]) + 'px'

				diver.style.width = (coordinates[2] - coordinates[0]) + 'px';
				diver.style.height = (coordinates[3] - coordinates[1]) + 'px';
				diver.style.overflow = 'hidden';
				page_ele.appendChild(diver);
			}
*/
/*
			spacerlist = jsonPath(response.pages.page[l], "$..spacer[*]")

			for (var j = 0; j < spacerlist.length; j++) {
				var spacer = spacerlist[j];
				var coordinates = spacer.attributes.bbox.split(',');

				var sp_ele = document.createElement("div");
				sp_ele.setAttribute('class', 'ss-spacer');
				sp_ele.style.position = 'absolute';

				sp_ele.style.left = (coordinates[0] - page_coords[0]) + 'px';
				sp_ele.style.top = (page_coords[3] - coordinates[3]) + 'px'

				sp_ele.style.width = (coordinates[2] - coordinates[0]) + 'px';
				sp_ele.style.height = (coordinates[3] - coordinates[1]) + 'px';
				sp_ele.style.overflow = 'hidden';
				page_ele.appendChild(sp_ele);

			}

			spacerlist = jsonPath(response.pages.page[l], "$..linespacer[*]")

			for (var j = 0; j < spacerlist.length; j++) {
				var spacer = spacerlist[j];
				var coordinates = spacer.attributes.bbox.split(',');

				var sp_ele = document.createElement("div");
				sp_ele.setAttribute('class', 'ss-linespacer');
				sp_ele.style.position = 'absolute';

				sp_ele.style.left = (page_coords[0]) + 'px';
				sp_ele.style.top = (page_coords[3] - coordinates[3]) + 'px'

				sp_ele.style.width = (page_coords[2] - page_coords[0]) + 'px';
				sp_ele.style.height = '1px';
				sp_ele.style.overflow = 'hidden';
				page_ele.appendChild(sp_ele);

			}
*/

			//main_viewer.appendChild(page_ele);
		}

    }});
};


function xmlToJson(xml) {

	// Create the return object
	var obj = {};

	if (xml.nodeType == 1) { // element
		// do attributes
		if (xml.attributes.length > 0) {
		obj["attributes"] = {};
			for (var j = 0; j < xml.attributes.length; j++) {
				var attribute = xml.attributes.item(j);
				obj["attributes"][attribute.nodeName] = attribute.nodeValue;
			}
		}
	} else if (xml.nodeType == 3) { // text
		obj = xml.nodeValue;
	}

	// do children
	if (xml.hasChildNodes()) {
		for(var i = 0; i < xml.childNodes.length; i++) {
			var item = xml.childNodes.item(i);
			var nodeName = item.nodeName;
			if (typeof(obj[nodeName]) == "undefined") {
				if (nodeName !== 'pages') {
					obj[nodeName] = [];
					obj[nodeName].push(xmlToJson(item));
				} else {
					obj[nodeName] = xmlToJson(item);
				}

			} else {
				if (typeof(obj[nodeName].push) == "undefined") {
					var old = obj[nodeName];
					obj[nodeName] = [];
					obj[nodeName].push(old);
				}
				obj[nodeName].push(xmlToJson(item));
			}
		}
	}
	return obj;
};

function findParentSize(containerSelector){
		var maxX = $(containerSelector).width(), maxY = $(containerSelector).height();

		$(containerSelector).children().each(function (i){
				if (maxX < parseInt($(this).css('left')) + $(this).width()){
						maxX = parseInt($(this).css('left')) + $(this).width();
				}
				if (maxY < parseInt($(this).css('top')) + $(this).height()){
						maxY = parseInt($(this).css('top')) + $(this).height();
				}
		});
		return {
				'width': maxX,
				'height': maxY
		}
};
