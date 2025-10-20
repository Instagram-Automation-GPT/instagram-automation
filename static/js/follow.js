/* follow.js */
(() => {
    'use strict';
  
    /* ------------------------------
     * Utilities
     * ------------------------------ */
  
    function getCookie(name) {
      const value = `; ${document.cookie}`;
      const parts = value.split(`; ${name}=`);
      if (parts.length === 2) return parts.pop().split(';').shift();
      return null;
    }
  
    async function safeFetchJSON(url, options = {}) {
      const res = await fetch(url, options);
      let data = null;
      try {
        data = await res.json();
      } catch (_) {
        // Non-JSON responses will fall back to null
      }
      if (!res.ok) {
        const msg = (data && data.message) || `Request failed with status ${res.status}`;
        throw new Error(msg);
      }
      return data;
    }
  
    function maskPassword(pw) {
      if (!pw) return '—';
      return '•'.repeat(Math.min(8, pw.length));
    }
  
    function setButtonLoading(btn, loadingText = 'Working...') {
      if (!btn) return () => {};
      const original = btn.innerHTML;
      btn.disabled = true;
      btn.innerHTML = `<i class="fas fa-spinner fa-spin mr-2"></i>${loadingText}`;
      return () => {
        btn.disabled = false;
        btn.innerHTML = original;
      };
    }
  
    /* ------------------------------
     * Bootstrap 5 tooltips init
     * (your HTML should use data-bs-toggle)
     * ------------------------------ */
    function initTooltips() {
      if (!window.bootstrap) return;
      const triggers = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
      triggers.forEach(el => new bootstrap.Tooltip(el));
    }
  
    /* ------------------------------
     * Modal open/close
     * ------------------------------ */
    function initModalControls() {
      const openBtn = document.getElementById('openModalButton');
      const closeBtn = document.getElementById('closeModalButton');
      const modal = document.getElementById('myModal');
  
      if (openBtn && modal) {
        openBtn.addEventListener('click', () => modal.classList.remove('hidden'));
      }
      if (closeBtn && modal) {
        closeBtn.addEventListener('click', () => modal.classList.add('hidden'));
      }
  
      // Optional: close when clicking backdrop
      if (modal) {
        modal.addEventListener('click', (e) => {
          if (e.target === modal) modal.classList.add('hidden');
        });
      }
    }
  
    /* ------------------------------
     * Extractor Registration (Login)
     * POST /follow_instagram_login/
     * Body: { username, password, twostepcode? } as JSON
     * ------------------------------ */
    function initRegistrationForm() {
      const form = document.getElementById('registrationForm');
      const modal = document.getElementById('myModal');
  
      if (!form) return;
  
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
  
        const submitBtn = e.submitter || form.querySelector('button[type="submit"]');
        const stopLoading = setButtonLoading(submitBtn, 'Registering...');
  
        try {
          const username = document.getElementById('username')?.value.trim();
          const password = document.getElementById('password')?.value;
          const twostepcode = document.getElementById('twostepcode')?.value.trim();
  
          if (!username || !password) {
            alert('Username and password are required.');
            return;
          }
  
          const payload = { username, password };
          if (twostepcode) payload.twostepcode = twostepcode;
  
          const headers = {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken') || ''
          };
  
          const data = await safeFetchJSON('/follow_instagram_login/', {
            method: 'POST',
            headers,
            body: JSON.stringify(payload),
            redirect: 'follow'
          });
  
          alert(data.message || 'Registered successfully.');
          // Refresh the extractors list if available
          fetchExtractors();
          // Close and reset
          modal?.classList.add('hidden');
          form.reset();
        } catch (err) {
          console.error('Registration error:', err);
          alert(`There was an error processing your registration. ${err.message || err}`);
        } finally {
          stopLoading();
        }
      });
    }
  
    /* ------------------------------
     * Search Users (getting target id)
     * POST /getting_user_id/
     * Body: { targetusername, number, category } as JSON
     * ------------------------------ */
    function initSearchForm() {
      const searchForm = document.getElementById('searchForm');
      const targetUsername = document.getElementById('targetUsername');
      const number = document.getElementById('number');
      const category = document.getElementById('category');
      const searchResults = document.getElementById('searchResults');
  
      if (!searchForm) return;
  
      searchForm.addEventListener('submit', async (event) => {
        event.preventDefault();
  
        const usernameValue = targetUsername?.value.trim();
        const numberValue = parseInt(number?.value, 10);
        const categoryValue = category?.value;
  
        // Basic validation
        if (!usernameValue) {
          alert('Username is required.');
          return;
        }
        if (isNaN(numberValue) || numberValue <= 0) {
          alert('Number must be greater than zero.');
          return;
        }
        if (!['fr', 'gb'].includes(categoryValue)) {
          alert('Category must be either "fr" or "gb".');
          return;
        }
  
        const stopLoading = setButtonLoading(searchForm.querySelector('button[type="submit"]'), 'Searching...');
  
        try {
          const headers = { 'Content-Type': 'application/json' };
          const body = JSON.stringify({
            targetusername: usernameValue,
            number: numberValue,
            category: categoryValue
          });
  
          // This endpoint returns text, not JSON
          const res = await fetch('/getting_user_id/', {
            method: 'POST',
            headers,
            body,
            redirect: 'follow'
          });
  
          const text = await res.text();
          if (!res.ok) {
            throw new Error(text || `Request failed with status ${res.status}`);
          }
  
          if (searchResults) {
            searchResults.innerHTML = `<pre class="whitespace-pre-wrap break-words">${text}</pre>`;
          }
        } catch (err) {
          console.error('Search error:', err);
          alert(`Search failed. ${err.message || err}`);
        } finally {
          stopLoading();
        }
      });
    }
  
    /* ------------------------------
     * Followers list + pagination
     * GET /showing_instagram_followers/
     * Response: { followers: [ { username, full_name, profile_pic_url, target_username, follow_category } ] }
     * ------------------------------ */
    const ITEMS_PER_PAGE = 10;
    let currentPage = 1;
    let followersList = [];
  
    function renderFollowers(page) {
      const userList = document.getElementById('userList');
      const paginationControls = document.getElementById('pagination-controls');
      if (!userList || !paginationControls) return;
  
      userList.innerHTML = '';
  
      const start = (page - 1) * ITEMS_PER_PAGE;
      const end = start + ITEMS_PER_PAGE;
      const paginatedFollowers = followersList.slice(start, end);
  
      paginatedFollowers.forEach((follower) => {
        const li = document.createElement('li');
        li.className = 'border-b border-gray-300 py-2';
        li.innerHTML = `
          <p><strong>Username:</strong> ${follower.username ?? '—'}</p>
          <p><strong>Full Name:</strong> ${follower.full_name ?? '—'}</p>
          <p><strong>Profile Pic:</strong> ${
            follower.profile_pic_url
              ? `<a href="${follower.profile_pic_url}" target="_blank" rel="noopener" class="text-blue-500 underline">View</a>`
              : '—'
          }</p>
          <p><strong>Target Username:</strong> ${follower.target_username ?? '—'}</p>
          <p><strong>Follow Category:</strong> ${follower.follow_category ?? '—'}</p>
        `;
        userList.appendChild(li);
      });
  
      // Pagination controls
      const totalPages = Math.ceil(followersList.length / ITEMS_PER_PAGE);
      paginationControls.innerHTML = '';
  
      // Prev
      const prevButton = document.createElement('button');
      prevButton.className = `px-3 py-1 mx-1 rounded ${page > 1 ? 'bg-gray-300 hover:bg-gray-400' : 'bg-gray-200 cursor-not-allowed'}`;
      prevButton.innerText = 'Prev';
      prevButton.disabled = page <= 1;
      prevButton.addEventListener('click', () => {
        if (currentPage > 1) {
          currentPage--;
          renderFollowers(currentPage);
        }
      });
      paginationControls.appendChild(prevButton);
  
      // Page numbers (up to 3 visible)
      let startPage = Math.max(1, page - 1);
      let endPage = Math.min(totalPages, page + 1);
      if (endPage - startPage < 2) {
        if (page - 1 < 1) {
          endPage = Math.min(totalPages, endPage + (2 - (endPage - startPage)));
        } else if (page + 1 > totalPages) {
          startPage = Math.max(1, startPage - (2 - (endPage - startPage)));
        }
      }
  
      for (let i = startPage; i <= endPage; i++) {
        const btn = document.createElement('button');
        btn.className = `px-3 py-1 mx-1 rounded ${i === page ? 'bg-blue-500 text-white' : 'bg-gray-300'}`;
        btn.innerText = i;
        btn.addEventListener('click', () => {
          currentPage = i;
          renderFollowers(currentPage);
        });
        paginationControls.appendChild(btn);
      }
  
      // Next
      const nextButton = document.createElement('button');
      nextButton.className = `px-3 py-1 mx-1 rounded ${page < totalPages ? 'bg-gray-300 hover:bg-gray-400' : 'bg-gray-200 cursor-not-allowed'}`;
      nextButton.innerText = 'Next';
      nextButton.disabled = page >= totalPages;
      nextButton.addEventListener('click', () => {
        if (currentPage < totalPages) {
          currentPage++;
          renderFollowers(currentPage);
        }
      });
      paginationControls.appendChild(nextButton);
    }
  
    async function fetchFollowersAndInitializePagination() {
      try {
        const data = await safeFetchJSON('/showing_instagram_followers/');
        if (data && Array.isArray(data.followers)) {
          followersList = data.followers;
          currentPage = 1;
          renderFollowers(currentPage);
        } else {
          console.error('Unexpected followers data format:', data);
        }
      } catch (err) {
        console.error('Error fetching followers:', err);
      }
    }
  
    /* ------------------------------
     * Extractors list
     * GET /showing_instagram_extractors_account/
     * Response: { username, password } (avoid showing raw pw)
     * ------------------------------ */
    async function fetchExtractors() {
      const extractorsList = document.getElementById('extractors-list');
      if (!extractorsList) return;
  
      try {
        const data = await safeFetchJSON('/showing_instagram_extractors_account/');
        extractorsList.innerHTML = '';
  
        if (data.username) {
          const sessionDiv = document.createElement('div');
          sessionDiv.innerHTML = `
            <p><strong>Username:</strong> ${data.username}</p>
            <p><strong>Password:</strong> ${maskPassword(data.password)}</p>
          `;
          extractorsList.appendChild(sessionDiv);
        } else {
          const emptyDiv = document.createElement('div');
          emptyDiv.textContent = 'No extractor account registered.';
          extractorsList.appendChild(emptyDiv);
        }
      } catch (err) {
        console.error('Error fetching extractor:', err);
        extractorsList.innerHTML = '<p class="text-red-600">Unable to load extractor account.</p>';
      }
    }
  
    /* ------------------------------
     * DOM Ready
     * ------------------------------ */
    document.addEventListener('DOMContentLoaded', () => {
      initTooltips();
      initModalControls();
      initRegistrationForm();
      initSearchForm();
      fetchFollowersAndInitializePagination();
      fetchExtractors();
    });
  })();
  