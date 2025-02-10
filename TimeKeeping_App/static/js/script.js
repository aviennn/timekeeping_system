async function fetchPhilippinesTime() {
  try {
      const response = await fetch('https://timeapi.io/api/Time/current/zone?timeZone=Asia/Manila');
      if (!response.ok) {
          throw new Error('Failed to fetch time');
      }
      const data = await response.json();
      return new Date(data.dateTime);
  } catch (error) {
      console.error('Error fetching time:', error);
      // Fallback to local time if API fails
      return new Date();
  }
}

async function updateClock() {
  try {
      const now = await fetchPhilippinesTime();
      
      // Format time (HH:MM:SS AM/PM)
      const timeOptions = { 
          hour: 'numeric',
          minute: '2-digit',
          second: '2-digit', // Ensure seconds are always displayed
          hour12: true
      };
      
      // Format date (Weekday, Month Day, Year)
      const dateOptions = {
          weekday: 'long',
          year: 'numeric',
          month: 'long',
          day: 'numeric'
      };

      const timeElement = document.getElementById('time');
      const dateElement = document.getElementById('date');

      if (timeElement && dateElement) {
          timeElement.textContent = now.toLocaleTimeString('en-US', timeOptions);
          dateElement.textContent = now.toLocaleDateString('en-US', dateOptions);
      }
  } catch (error) {
      console.error('Error updating clock:', error);
  }
}

// Initialize clock
document.addEventListener('DOMContentLoaded', () => {
  // Initial update
  updateClock();
  
  // Update every second
  setInterval(updateClock, 1000);
});

function togglePassword() {
    const passwordField = document.getElementById('password');
    const eyeIcon = document.getElementById('eye-icon');
    if (passwordField.type === 'password') {
        passwordField.type = 'text';
        eyeIcon.classList.replace('fa-eye', 'fa-eye-slash'); 
    } else {
        passwordField.type = 'password';
        eyeIcon.classList.replace('fa-eye-slash', 'fa-eye'); 
    }
}

let mybutton = document.getElementById("btn-back-to-top");

window.onscroll = function () {
  scrollFunction();
};

function scrollFunction() {
  if (
    document.body.scrollTop > 20 ||
    document.documentElement.scrollTop > 20
  ) {
    mybutton.style.display = "block";
  } else {
    mybutton.style.display = "none";
  }
}

mybutton.addEventListener("click", backToTop);

function backToTop() {
  document.body.scrollTop = 0;
  document.documentElement.scrollTop = 0;
}