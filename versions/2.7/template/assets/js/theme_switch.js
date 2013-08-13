
// Theme Name
var theme = 'theme-openshift';

// Elements
var html = document.getElementsByTagName('html')[0];
var logo = document.getElementsByClassName('logo')[0];

// Apply theme if it was saved in localStorage
if( localStorage.theme === theme ){
  html.classList.add( theme );
}


// Click handler to toggle the theme
logo.onclick = function(){
  var isActive = html.classList.toggle( theme );
  localStorage.theme = isActive ? theme : null;
};

