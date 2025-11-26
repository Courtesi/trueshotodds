 Option 2: Automated (Shell Script)

  Create a helper script in root: update-submodule.sh

  #!/bin/bash
  # Usage: ./update-submodule.sh backend "commit message"

  SUBMODULE=$1
  MESSAGE=$2

  if [ -z "$SUBMODULE" ] || [ -z "$MESSAGE" ]; then
      echo "Usage: ./update-submodule.sh <submodule> <message>"
      exit 1
  fi

  # Go to submodule and push
  cd "$SUBMODULE" || exit 1
  git push origin main

  # Go back to root and update pointer
  cd ..
  git add "$SUBMODULE"
  git commit -m "chore: update $SUBMODULE - $MESSAGE"
  git push origin main

  echo "✓ Updated $SUBMODULE submodule pointer in root"

  Usage:
  chmod +x update-submodule.sh
  ./update-submodule.sh backend "added pre-commit hooks"

  Option 3: Update All Submodules at Once

  # Update all submodules to their latest main branch
  git submodule foreach 'git pull origin main'

  # Commit all updates in root
  git add .
  git commit -m "chore: update all submodules to latest"
  git push

  Common Scenarios

  Scenario 1: Deploy to Production

  # 1. Make sure all submodules are pushed
  cd backend && git push && cd ..
  cd webscraper && git push && cd ..
  cd frontend && git push && cd ..

  # 2. Update root to point to latest
  git submodule update --remote
  git add .
  git commit -m "chore: update all submodules for production deploy"
  git push

  # 3. Deploy using root repository
  # Your docker-compose.yml will use the submodules at the committed versions

  Scenario 2: Rollback a Submodule

  # Go to the submodule
  cd backend

  # Find the commit you want
  git log

  # Reset to that commit
  git reset --hard abc123

  # Push (might need force)
  git push origin main --force

  # Update root pointer
  cd ..
  git add backend
  git commit -m "chore: rollback backend to abc123"
  git push

  Scenario 3: Clone Fresh (New Developer)

  # Clone with submodules
  git clone --recurse-submodules https://github.com/user/trueshotodds_v2.git

  # Or if already cloned without submodules
  git clone https://github.com/user/trueshotodds_v2.git
  cd trueshotodds_v2
  git submodule init
  git submodule update

  Best Practices

  1. Always push submodule first, then update root
  cd backend
  git push  # ← Do this first!
  cd ..
  git add backend && git commit -m "update backend"
  git push  # ← Then this
  2. Use descriptive commit messages in root for submodule updates
  git commit -m "chore: update backend - added pre-commit hooks and README"
  3. Keep submodules on main branch (or track specific branches)
  # Ensure submodules track main
  git config -f .gitmodules submodule.backend.branch main
  git config -f .gitmodules submodule.webscraper.branch main
  git config -f .gitmodules submodule.frontend.branch main
  4. Check submodule status before deploying
  git submodule status
  # Ensure no + (uncommitted changes) or - (not initialized)

  Your .gitmodules File

  Should look something like:
  [submodule "backend"]
      path = backend
      url = https://github.com/Courtesi/tso_backend.git
      branch = main

  [submodule "webscraper"]
      path = webscraper
      url = https://github.com/Courtesi/tso_webscraper.git
      branch = main

  [submodule "frontend"]
      path = frontend
      url = https://github.com/Courtesi/tso_frontend.git
      branch = main

  Quick Cheat Sheet

  # Update root to latest submodule commits
  git submodule update --remote --merge

  # Show which commit each submodule is at
  git submodule status

  # Commit submodule pointer updates
  git add <submodule-name>
  git commit -m "chore: update <submodule-name>"

  # Pull everything (root + submodules)
  git pull --recurse-submodules

  # Push submodule changes first, then root
  cd <submodule> && git push && cd .. && git add <submodule> && git commit && git push

  Does this help clarify the workflow? Any specific scenario you want me to elaborate on?