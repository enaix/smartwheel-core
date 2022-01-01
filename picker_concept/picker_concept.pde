int cx = 350; // center point
int cy = 350; // center point
float alpha = 225; // 3.0 * 3.14 / 4.0;
float f_alpha = alpha;
int c = 0;
float angle = 0;
int hue_selection = 0;
int sat_selection = 360;
float sat_wheel = alpha;
int bri_selection = 360;
float bri_wheel = alpha;
int selectMode = 0;
boolean fillCenter = true;

void setup() 
{
  size(700, 700);
  colorMode(HSB, 360, 360, 360);  
  background(0);
  strokeWeight(1);
}

float getX(float a, int w){
  return cos(radians(a))*w/2 + cx;
}

float getY(float a, int h){
  return sin(radians(a))*h/2 + cy;
}

void drawCircle(float start){
  strokeWeight(0.1);
  float a = start;
  int col = 0;
  while(a <= 360 + start){
    fill(col, 360, 360, 360);
    stroke(col, 360, 360, 360);
    triangle(cx, cy, getX(a-1, 500), getY(a-1, 500), getX(a+1, 500), getY(a+1, 500));
    col += 1;
    a += 1;
  }
}

void drawBorder(int w, int c) {
  float a = 0;
  strokeWeight(0);
  fill(0, 0, 0);
  stroke(0, 0, 0);
  while(a <= 360) {
    circle(getX(a, c), getY(a, c), w);
    a += 1;
  }
}

void drawSpectrum(float start, int start_w, int end_w, int[] col_start, int[] delta) {
  float a = start;
  strokeWeight(4);
  int[] col = col_start;
  while(a <= 360 + start){
    fill(col[0], col[1], col[2]);
    stroke(col[0], col[1], col[2]);
    line(getX(a, start_w), getY(a, start_w), getX(a, end_w), getY(a, end_w));
    a += 0.5;
    if (a % 1 == 0) {
      for(int i = 0; i < col.length; i+=1) {
        col[i] += delta[i];
      }
    }
  }
}

void drawTriangle(float a, int start_w, int end_w) {
  strokeWeight(1);
  fill(0, 0, 0);
  stroke(0, 0, 0);
  triangle(getX(a, start_w), getY(a, start_w), getX(a-2, end_w), getY(a-2, end_w), getX(a+2, end_w), getY(a+2, end_w));
}

void mouseWheel(MouseEvent event) {
  float e = event.getCount();
  float a = e * 5;
  int wheel = 0;
  switch(selectMode){
    case(0):
      wheel = hue_selection;
      alpha += a;
      break;
    case(1):
      wheel = sat_selection;
      sat_wheel += a;
      break;
    case(2):
      wheel = bri_selection;
      bri_wheel += a;
      break;
  }
  wheel -= e * 5;
  if (wheel < 0) {
    wheel = 360 + wheel;
  } else {
    if (wheel > 360) {
      wheel -= 360;
    }
  }
  switch(selectMode){
    case(0):
      hue_selection = wheel;
      break;
    case(1):
      sat_selection = wheel;
      break;
    case(2):
      bri_selection = wheel;
      break;
  }
}

void mousePressed() {
  if(mouseButton == CENTER) {
    selectMode = (selectMode + 1) % 3;
  }
}

void drawCurve(float a, int start_w, int end_w, int d) {
  strokeWeight(1);
  fill(0, 0, 0);
  stroke(0, 0, 0);
  beginShape();
  curveVertex(getX(a-2.5, start_w), getY(a-2.5, start_w));
  curveVertex(getX(a-2.5, start_w), getY(a-2.5, start_w));
  curveVertex(getX(a-0.2, (end_w + start_w)/2), getY(a-0.2, (end_w + start_w)/2));
  curveVertex(getX(a-2.5, end_w), getY(a-2.5, end_w));
  curveVertex(getX(a+2.5, end_w), getY(a+2.5, end_w));
  curveVertex(getX(a+0.25, (end_w + start_w)/2), getY(a+0.25, (end_w + start_w)/2));
  curveVertex(getX(a+2.5, start_w), getY(a+2.5, start_w));
  curveVertex(getX(a+2.5, start_w), getY(a+2.5, start_w));
  endShape();
}

void draw() 
{
  drawCircle(alpha);
  drawBorder(50, 500-45);
  if(fillCenter) {
    fill(0, 0, 0);
    strokeWeight(1);
    circle(cx, cy, 350);
    stroke(360, 0, 360);
    fill(hue_selection, sat_selection, bri_selection);
    square(cx - 40, cy - 125, 80);
    fill(0, 0, 360);
    textSize(32);
    textAlign(CENTER);
    text("(" + str(hue_selection) + "; " + str(sat_selection) + "; " + str(bri_selection) + ")", cx, cy);
  }
  if (selectMode == 0) {
    drawTriangle(f_alpha, 500-110, 500-95);
  }
  int[] colorHue = {hue_selection, 0, 360};
  int[] colorDelta = {0, 1, 0};
  drawSpectrum(sat_wheel, 500-70, 500-10, colorHue, colorDelta);
  drawBorder(10, 500-70);
  drawBorder(10, 500-10);
  drawCurve(sat_wheel, 500-60, 500-13, 0);
  if (selectMode == 1) {
    drawTriangle(f_alpha, 500-35, 500-15);
  }
  colorHue[1] = sat_selection;
  colorHue[2] = 0;
  colorDelta[1] = 0;
  colorDelta[2] = 1;
  drawSpectrum(bri_wheel, 510, 570, colorHue, colorDelta);
  drawBorder(10, 510);
  drawBorder(10, 570);
  drawCurve(bri_wheel, 520, 567, 0);
  if (selectMode == 2) {
    drawTriangle(f_alpha, 545, 565);
  }
}
