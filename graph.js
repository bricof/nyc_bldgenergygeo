
// context

var dataFilePath = "bldgsenergytopo.json";
var svgID = "graph-svg-id";
var width = 750;
var height = 350;


// configuration variables

var textids = ["text_address","text_type","text_floorArea","text_roofHeight","text_siteEUI",
               "text_sourceEUI","text_energyStar","text_GHG"];

var textprefixes = ["Address : ","Primary Type : ","Floor Area (ft2) : ",
                    "Roof Height (ft): ","Site EUI (kBtu/ft2) : ",
                    "Source EUI (kBtu/ft2) : ","ENERGY STAR Score : ",
                    "Total GHG Emissions (MtCO2e) : "];

var textproperties = ["Address", "Primary Property Type - Self Selected",
                      "Property Floor Area (Buildngs and Parking)(ft2)",
                      "HEIGHT_ROO", "Site EUI(kBtu/ft2)", 
                      "Weather Normalized Source EUI(kBtu/ft2)", "ENERGY STAR Score", 
                      "Total GHG Emissions(MtCO2e)"];

var selecttext = ["Site EUI", "Source EUI", "Energy Star", "Total GHG"];

var selectids = ["select_site", "select_source", "select_energyStar", "select_GHG"];

var propertyOptions = ["Site EUI(kBtu/ft2)", "Weather Normalized Source EUI(kBtu/ft2)", 
                       "ENERGY STAR Score", "Total GHG Emissions(MtCO2e)"];

var scaleMax = [250, 400, 0, 50000];
var scaleMin = [0, 0, 100, 0];
var scaleUnit = ["kBtu/ft2","kBtu/ft2","Score","MtCO2e"];

var selectedNum = 3;


// map projection

var projection = d3.geo.mercator()
    .center([-112.6717, 48.1217])
    .scale(1500000)
    .translate([width / 2, height / 2]);


// svg select

var svg = d3.select("#" + svgID);

              
// color scale

var colorDomain = function(n) {
    var cdom = [];
    for (var i=0; i<6; i++){
        cdom.push( scaleMin[n] + (scaleMax[n] - scaleMin[n]) * (i / 5.0) );
    }
    cdom.push( (scaleMax[n] - scaleMin[n]) * 1000000 );
    return cdom;
}

var colorRange = ["#ffffb2","#fed976","#feb24c","#fd8d3c","#fc4e2a","#e31a1c","#b10026"];
    
var color = d3.scale.linear()
    .domain(colorDomain(selectedNum))
    .range(colorRange);


// legend

var legendUnitWidth = 28;
for (var i=0; i<colorRange.length; i++) {
    svg.append("rect")
        .attr("x", 500 + i * legendUnitWidth).attr("y",80)
        .attr("height",10).attr("width",legendUnitWidth)
        .style("fill", color(colorDomain(selectedNum)[i]));
}
svg.append("rect")
    .attr("x", 500 + colorRange.length * legendUnitWidth + 10).attr("y",80)
    .attr("height",10).attr("width",legendUnitWidth)
    .style("fill", "#f0f0f0");

svg.append("text")
    .attr("x", 500).attr("y", 75)
    .attr("font-size", "10px")
    .attr("id", "legendMin")
    .text( scaleMin[selectedNum]);

svg.append("text")
    .attr("x", 500 + colorRange.length * legendUnitWidth).attr("y", 75)
    .attr("font-size", "10px")
    .attr("text-anchor", "end")
    .attr("id", "legendMax")
    .text( scaleMax[selectedNum]);

svg.append("text")
    .attr("x", 500 + colorRange.length * legendUnitWidth / 2).attr("y", 75)
    .attr("font-size", "10px")
    .attr("text-anchor", "middle")
    .attr("id", "legendUnit")
    .text( scaleUnit[selectedNum]);

svg.append("text")
    .attr("x", 500 + (colorRange.length + 0.5) * legendUnitWidth + 10).attr("y", 75)
    .attr("font-size", "10px")
    .attr("text-anchor", "middle")
    .text( "NA" );


// text fields for details on hover

for (var i=0; i<textids.length; i++) {
    svg.append("text")
        .attr("x", 500).attr("y", 190 + i * 20)
        .attr("font-size", "10px")
        .attr("id", textids[i])
        .style("opacity", (i == textids.length - 1) ? 1 : 1e-6)
        .text( (i == textids.length - 1) ? 'Hover over buildings for details' : '' );
}
  

// data file read

d3.json(dataFilePath, function(error, bldgs) {


  // drawing of map

  svg.selectAll("path")
      .data(topojson.feature(bldgs, bldgs.objects.bldgsenergygeo).features)
    .enter().append("path")  
      .attr("d", d3.geo.path().projection(projection))
      .style("fill", function(d) { 
          return (d.properties[propertyOptions[selectedNum]] == null || d.properties[propertyOptions[selectedNum]] == "Exempt") ? "#f0f0f0" : color(d.properties[propertyOptions[selectedNum]]);
        })
      .on('mouseover', function(d){
            for (var i=0; i<textids.length; i++) {
                d3.select("#" + textids[i])
                    .text(textprefixes[i] + d.properties[textproperties[i]])
                    .transition()
                      .duration(200)
                      .style("opacity", 1);
            }
          })
      .on('mouseout', function(d){
            for (var i=0; i<textids.length; i++) {
                d3.select("#" + textids[i])
                    .transition()
                      .duration(1500)
                      .style("opacity", 1e-6);
            }
          });


  // text fields used as map type selectors

  for (var i=0; i<selectids.length; i++) {
    svg.append("text").attr("x", 500 + (selectids.length - i - 1) * 65).attr("y", 40)
        .attr("class", "text-button")
        .attr("id", selectids[i]).style("opacity", i == 3 ? 1 : 0.5 )
        .attr("iv", i)
        .attr("font-size", "10px")
        .text(selecttext[i])
        .on('mouseover', function(e){
                
                // determine which text-'button' is selected
                var selectedNum = parseInt(d3.select(this)[0][0].attributes.iv.value);

                // change opacities of text-'buttons'
                d3.selectAll(".text-button").style("opacity",0.5);
                d3.select(this).style("opacity",1);
                
                // update legend labels
                d3.select("#legendMin").text(scaleMin[selectedNum]);
                d3.select("#legendMax").text(scaleMax[selectedNum]);
                d3.select("#legendUnit").text(scaleUnit[selectedNum]);
                
                // update colors in map
                color.domain(colorDomain(selectedNum));
                svg.selectAll("path")
                  .transition()
                    .duration(1000)
                    .style("fill", function(d) {
                        return (d.properties[propertyOptions[selectedNum]] == null || d.properties[propertyOptions[selectedNum]] == "Exempt") ? "#f0f0f0" : color(d.properties[propertyOptions[selectedNum]]);
                      });

          });
  }


});




