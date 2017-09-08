# !/usr/bin/python
# -*- coding: UTF-8 -*-

'''
# Usage
--help is available
'-t','--inputtemplate', Input table block template string.
'-p','--productlist', Product list JSON format line: "{\"id\": [number], \"date\":"[release date]", \"categ\":"[category]", \"name\":"[name]", \"link\":"[any link]", \"image\": \"[path to image]\", \"w\": [cell width], \"h\": [cell height], \"desc\": \"[any description]\"}"
'''

import argparse
import json

modal_template = '''
<div class="modal" id="modal_{id}" role="dialog" style="display: none;">
  <div class="container">
    <div class="modal-header">
        <div class="close-modal" data-dismiss="modal">
            <div class="lr">
                <div class="rl">
                </div>
            </div>
        </div>
      <h2 class="modal-title">{name}</h2>
    </div>
    <div class="row">
        <div class="col-lg-8 col-lg-offset-2">
            <div class="modal-body">
                <a href="{link}" target="_blank"><img class="image oe_product_image" src="{image}"></a>
                <p><a href="{link}" target="_blank">{link}</a></p>
                <p>{desc}</p>
                <ul class="list-inline item-details">
                        <li>Category: <strong>{categ}</strong> </li>
                        <li>Release date: <strong>{date}</strong> </li>
                    </ul>
                <div class="modal-footer" style="margin:30px 0 0"></div>
                <button type="button" class="btn btn-default" data-dismiss="modal"><i class="fa fa-times"></i> Close</button>
            </div>
        </div>
    </div>
  </div>
</div> 
'''

html_template = '''
<section>
  <div class="container products_grid">
      <table width='100%%'>
       <tbody>
        %s
       </tbody>
      </table>
  </div>
</section>
  %s
'''


class TableCompute(object):
    def __init__(self):
        self.table = {}

    def _check_place(self, posx, posy, sizex, sizey):
        res = True
        for y in range(sizey):
            for x in range(sizex):
                if posx + x >= PPR:
                    res = False
                    break
                row = self.table.setdefault(posy + y, {})
                if row.setdefault(posx + x) is not None:
                    res = False
                    break
            for x in range(PPR):
                self.table[posy + y].setdefault(x, None)
        return res

    def process(self, products):
        # Compute products positions on the grid
        minpos = 0
        index = 0
        maxy = 0
        for p in products:
            x = min(max(p['w'], 1), PPR)
            y = min(max(p['h'], 1), PPR)
            if index >= PPG:
                x = y = 1
            pos = minpos
            while not self._check_place(pos % PPR, pos / PPR, x, y):
                pos += 1
            if index >= PPG and ((pos + 1.0) / PPR) > maxy:
                break

            if x == 1 and y == 1:  # simple heuristic for CPU optimization
                minpos = pos / PPR

            for y2 in range(y):
                for x2 in range(x):
                    self.table[(pos / PPR) + y2][(pos % PPR) + x2] = False
            self.table[pos / PPR][pos % PPR] = {
                'product': p,
                'x': x,
                'y': y
            }
            if index <= PPG:
                maxy = max(maxy, y + (pos / PPR))
            index += 1

        # Format table according to HTML needs
        rows = self.table.items()
        rows.sort()
        rows = map(lambda x: x[1], rows)
        for col in range(len(rows)):
            cols = rows[col].items()
            cols.sort()
            x += len(cols)
            rows[col] = [c for c in map(lambda x: x[1], cols) if c != False]

        return rows


# Parsers
parser = argparse.ArgumentParser(
    prog='Mosaic constructor',
    description='This script is used for mosaic table constructing with different size blocs'
)
parser.add_argument('-t', '--inputtemplate',
                    help='Required argument. Input table block template string, example pattern <td> ... </td>. May be splitted for several lines',
                    required=True, nargs='+')
parser.add_argument('-p', '--productlist',
                    help='Required argument. JSON format line: "{\"id\": [number], \"link\":"[any link]", \"image\": \"[path to image]\", \"w\": [cell width], \"h\": [cell height], \"desc\": \"[any description]\"}"',
                    required=True, nargs='+')
args = parser.parse_args()
inp = args.inputtemplate
pl = args.productlist
OBJECTS = [json.loads(p) for p in pl]
cell_template = '\n'.join(inp)
PPR = 12  # Products Per Row
PPG = 100  # Products Per Page


def css_compute():
    resulting = ['<style type="text/css">']
    res_fa = ['@media (min-width: 769px) and (max-width: 992px) {\n']
    for i in range(1, 13):
        size = i <= 2 and 12 or 20 + 5 * (i - 3)

        str_title = '.font-title-' + str(i) + ' {\n' + 'font-size: ' + str(size) + 'px;' + '\n' + '}'
        str_info = '.font-info-' + str(i) + ' {\n' + 'font-size: ' + str(size) + 'px;' + '\n' + '}'
        str_fa = i <= 2 and '.fa-margin-' + str(i) + ' {\n' + 'margin: ' + '4%;' + '\n' + '}' \
                 or i <= 4 and '.fa-margin-' + str(i) + ' {\n' + 'margin: ' + '10%;' + '\n' + '}' \
                 or '.fa-margin-' + str(i) + ' {\n' + 'margin: ' + '17%;' + '\n' + '}'
        resulting.append(str_title + '\n' + str_info)
        res_fa.append(str_fa)
    return '\n'.join(resulting) + '\n' + '\n'.join(res_fa) + '\n' + '}' + '\n' + '</style>'


def mosaic():
    bin = TableCompute().process(OBJECTS)
    html = []
    modal = []
    html.append('''<tr>''')
    for i in range(0, PPR):
        html.append('''<td width='{td_width}'></td>'''.format(td_width=str(100 / PPR) + '%'))
    html.append('''</tr>''')
    for p in bin:
        html.append('''<tr>''')
        for pp in p:
            if pp is not None:
                pp['product']['obj_colspan'] = str(pp['x'])
                pp['product']['obj_rowspan'] = str(pp['y'])
                pp['product']['obj_class'] = "oe_product oe_grid oe-height-" + str(pp['y'])
                temp = cell_template.format(**pp['product'])
                temp2 = modal_template.format(**pp['product'])
                html.append(temp)
                modal.append(temp2)
            else:
                html.append('''<td class="oe_product oe_grid oe-height-1"/>''')
        html.append('''</tr>''')
    html = '\n'.join(html)
    modal = '\n' + '<section id="portfolio modals">' + '\n'.join(modal) + '</section>'
    html = html_template % (html, modal)
    # inserting css styles in the beginning of 'html' and printing the result
    html = css + css_compute() + html
    print html


css = '''
 <style type="text/css">
@charset "utf-8";
/* ---- Default Styles ---- */
.oe_product {
  position: relative;
  border: 2px solid rgba(255, 255, 255, 0);
  border-collapse: separate;
  overflow: hidden;
}
.oe_product .oe_product_image {
  position: absolute;
  left: 0px;
  right: 0px;
  top: 0px;
  bottom: 0px;
  text-align: center;
}
.modal-body .oe_product_image {
  position: relative;
  width: 80%;
  height: 80%;
  left: 0px;
  right: 0px;
  top: 0px;
  bottom: 0px;
  text-align: center;
}
.oe_product .oe_product_image img{
  height: 100%;
  width: 100%;
  margin: auto;
  position: absolute;
  top: 0;
  left: 0;
  bottom: 0px;
  right: 0;
  z-index: 2;
}
@media (max-width: 768px) {
  .products_grid table, .products_grid tbody, .products_grid tr, .products_grid td {
    width: 100%;
    overflow: hidden;
  }
  .products_grid .oe_product {
    width: 100%;
    height: 300px;
    display: inline-block;
    overflow: hidden;
  }
}
@media (max-width: 450px) {
  .products_grid .oe_product {
    width: 100%;    
    height: 270px;
    display: inline-block;
    overflow: hidden;
  }
}
@media (min-width: 769px) {
  .products_grid tr {
    height: 62px;
    overflow: hidden;
  }
}
@media (min-width: 992px) {
  .products_grid tr {
    height: 81px;
    overflow: hidden;
  }
}
@media (min-width: 1200px) {
  .products_grid tr {
    height: 97px;
    overflow: hidden;
  }
}
@media (min-width: 769px) {
  .oe-height-1 {
    height: 62px;
  }
  .oe-height-2 {
    height: 124px;
  }
  .oe-height-3 {
    height: 186px;
  }
  .oe-height-4 {
    height: 248px;
  }
  .oe-height-5 {
    height: 310px;
  }
  .oe-height-6 {
    height: 372px;
  }
  .oe-height-7 {
    height: 434px;
  }
  .oe-height-8 {
    height: 496px;
  }
  .oe-height-9 {
    height: 558px;
  } 
  .oe-height-10 {
    height: 620px;
  }
  .oe-height-11 {
    height: 682px;
  }
  .oe-height-12 {
    height: 744px;
  }
}
@media (min-width: 992px) {
  .oe-height-1 {
    height: 81.11px;
  }
  .oe-height-2 {
    height: 161.11px;
  }
  .oe-height-3 {
    height: 243.33px;
  }
  .oe-height-4 {
    height: 324px;
  }
  .oe-height-5 {
    height: 405.55px;
  }
  .oe-height-6 {
    height: 483.33px;
  }
  .oe-height-7 {
    height: 564.44px;
  }
  .oe-height-8 {
    height: 645.56px;
  }
  .oe-height-9 {
    height: 726.22px;
  } 
  .oe-height-10 {
    height: 811px;
  }
  .oe-height-11 {
    height: 892px;
  }
  .oe-height-12 {
    height: 973px;
  }
}
@media (min-width: 1200px) {
  .oe-height-1 {
    height: 97px;
  }
  .oe-height-2 {
    height: 193px;
  }
  .oe-height-3 {
    height: 293px;
  }
  .oe-height-4 {
    height: 388px;
  }
  .oe-height-5 {
    height: 489px;
  } 
  .oe-height-6 {
    height: 583px;
  }
  .oe-height-7 {
    height: 684px;
  }
  .oe-height-8 {
    height: 778px;
  }
  .oe-height-9 {
    height: 870px;
  } 
  .oe-height-10 {
    height: 968px;
  }
  .oe-height-11 {
    height: 1065px;
  }
  .oe-height-12 {
    height: 1163px;
  }
}
.thumbs {
  position: relative;
  width: 100%;
  height: 100%;
  margin: 0;
  opacity: .99;
  overflow: hidden;
  cursor: pointer;
}
.thumbs a {
  text-decoration:none;
  border: 0;
  outline: 0;
}
.thumbs:before {
  content: '';
  background: rgba( 0, 0, 0, 0.6);
  width: 100%;
  height: 100%;
  opacity: 0;
  position: absolute;
  top: 0;
  left: 0;
  bottom: 0;
  z-index: 3;
  transition: .5s ease;
  -moz-transition: .5s ease;
  overflow: hidden;
}
.thumbs .caption {
  width: 100%;
  color: #fff;
  position: absolute;
  z-index: 4;
  text-align: center;
  overflow: hidden;
  text-decoration:none;
  height: 100%;
  width: 100%;
}
.thumbs .caption a {
  text-decoration:none;
  border: 0;
  outline: 0;
}
.thumbs .caption span {
  display: block;
  opacity: 0;
  position: relative;
  color: white;
}
.thumbs .caption .title {
  font-weight: normal;
  color: white;
  line-heght: 2.6em;
  padding-top: 18%;
￼ min-height: 100%;
￼ width: 100%;
￼ position: absolute;
}
.thumbs .caption .title {
  font-weight: normal;
  color: white;
  line-heght: 2.6em;
  padding-top: 18%;
￼ min-height: 100%;
￼ width: 100%;
￼ position: absolute;
}
@media (max-width: 768px) and (min-width: 450px){
  .thumbs .caption .title {
    font-weight: normal;
    color: white;
    line-heght: 2.6em;
    padding-top: 5%;
￼   min-height: 100%;
￼   width: 100%;
￼   position: absolute;
  }
}
.thumbs:focus:before,
.thumbs:focus span, .thumbs:hover:before,
.thumbs:hover span {
  opacity: 1;
  overflow: hidden;
}
.thumbs:focus:before, .thumbs:hover:before {
  overflow: hidden;
}
.thumbs:focus span, .thumbs:hover span {
  overflow: hidden;
}
.modal {
    position: fixed;
    top: 0;
    right: 0;
    bottom: 0;
    left: 0;
    z-index: 1050;
    display: none;
    overflow: hidden;
    outline: 0;
    background: white;
}
.modal-body {
    text-align: center;
    margin: 0;
}
.modal-header {
  padding: @modal-title-padding;
  border-bottom: 0;
  &:extend(.clearfix all);
}
.modal-header h2 {
    padding: 100px 0 0;
    min-height: 100%;
    border: 0;
    text-align: center;
    margin: 0;
    font-size: 3em;
}
.modal-body img {
    margin-bottom: 30px;
}
.modal-content .item-details {
    margin: 30px 0;
}
.close-modal {
    position: absolute;
    top: 25px;
    right: 25px;
    width: 75px;
    height: 75px;
    background-color: transparent;
    cursor: pointer;
}
.close-modal:hover {
    opacity: .3;
}
.close-modal .lr {
    z-index: 1051;
    width: 1px;
    height: 75px;
    margin-left: 35px;
    background-color: #2c3e50;
    -webkit-transform: rotate(45deg);
    -ms-transform: rotate(45deg);
    transform: rotate(45deg);
}
.close-modal .lr .rl {
    z-index: 1052;
    width: 1px;
    height: 75px;
    background-color: #2c3e50;
    -webkit-transform: rotate(90deg);
    -ms-transform: rotate(90deg);
    transform: rotate(90deg);
}
@media (min-width: 993px) {
  .caption .fa {
  position: relative;
  vertical-align: middle;
  line-height: 1;
  margin: 18%;
  }
}
@media (max-width: 768px) {
  .caption .title, .caption .info {
  color: white;
  font-size: 30px !important;
  line-heght: 1em;
￼ min-height: 100%;
￼ width: 100%;
￼ position: absolute;
  }
  .caption .fa {
  position: relative;
  vertical-align: middle;
  line-height: 1;
  margin: 8%;
  }
}
.thumbs .caption .fa:before {
    content: '\\f00e';
    color: white;
    display: inline-block;
    font-weight: normal;
    font-size: 22px;
    line-height: 1.2;
    font-family: FontAwesome;
    font-style: normal;
    font-weight: normal;
    text-decoration: inherit;
    text-rendering: auto;
    text-decoration: none;
}
</style>
'''
mosaic()
