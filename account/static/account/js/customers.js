fetch('/api/customers/')
  .then(response => response.json())
  .then(customers => {
      let ul = document.getElementById('customer-list');
      ul.innerHTML = "";

      customers.forEach(c => {
          ul.innerHTML += `<li>${c.name} - ${c.phone}</li>`;
      });
  })
  .catch(err => console.error("Hata:", err));
